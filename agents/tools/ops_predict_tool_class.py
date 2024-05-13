import time
import requests
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate

from langchain.tools import BaseTool
from paramslist import DEFAULT_TARGET_DATE, DEFAULT_HISTORY_DAYS, OPS_PREDICT_API_URL, PREDICT_ALARM_FILE_FOLDER,MAX_REINPUT_CNT
from paramslist import OPENAI_API_KEY_QW, OPENAI_API_BASE_QW, MODEL_NAME


class OpsPredictTool(BaseTool):
    name = "ops_predict_tool"
    station_info = "Unknown"
    retirement_rate = "Unknown"
    return_direct = True
    description = """
    此工具用于预测 基站退服概率。
    此工具根据用户输入的信息，提取目标基站名称和预测目标日期，预测指定目标基站的退服概率。
    工具输入是一段文本字符串，请将用户的输入[input]直接作为工具的输入[Action Input]以免损失信息。
    工具输出 预测的退服概率retirement_rate和基站相关信息。
        retirement rate是一个小数表示的概率。
        基站相关信息中包含基站的ID、名称（name）、运营商(vendor)、网络类型（net type）、所在省市（province，city）和基站的历史告警列表（alarm list）。
    请将工具的输出直接返回给用户以免损失信息。
    
    例如,当输入为[请分析沈阳大东区上园路7号-上园路13-1号051178TDD-HLY基站未来的退服概率]时, 可以调用此工具解决问题.
    """
    # 输入示例：target_date=[target_date or ‘Unknown’], node_name=[node_name or ‘Unknown’]。
    # 工具的输入是一段文本字符串 input_text，其中包含的信息有：1. target_date，是预测目标的日期; 2.node_name，是预测目标基站名称，为一串中文+符号+大写英文字母组成的字符串；
    def check_date(self, input_dict: dict) -> dict:
        print(input_dict)
        # 若未指定历史数据时间窗口， 根据提供的/默认的预测目标和历史窗口天数，设置历史数据时间窗口范围
        if input_dict.get("end_date") == 'Unknown' and input_dict.get("start_date") == 'Unknown':
            if input_dict.get("target_date") == 'Unknown':
                input_dict["target_date"] = DEFAULT_TARGET_DATE
            if input_dict.get("history_range_days") == 'Unknown':
                input_dict["history_range_days"] = DEFAULT_HISTORY_DAYS
            # print("in both Unknown")
            structured_target = time.strptime(input_dict.get("target_date"), "%Y-%m-%d")
            end_ts = time.mktime(structured_target) - 24 * 3600
            start_ts = time.mktime(structured_target) - 24 * 3600 * int(input_dict["history_range_days"])
            input_dict["end_date"] = time.strftime("%Y-%m-%d", time.localtime(end_ts))
            input_dict["start_date"] = time.strftime("%Y-%m-%d", time.localtime(start_ts))

        # 若仅指定历史数据时间窗口的第一天，根据提供的/默认的预测目标和历史窗口天数，设置历史数据时间窗口的最后一天（若指定了预测目标，优先使用预测目标前一天为窗口最后一天；否则根据历史窗口天数和历史窗口第一天计算）
        elif input_dict.get("end_date") == 'Unknown':
            if input_dict.get("target_date") != 'Unknown':
                structured_target = time.strptime(input_dict.get("target_date"), "%Y-%m-%d")
                end_ts = time.mktime(structured_target) - 24 * 3600
                input_dict["end_date"] = time.strftime("%Y-%m-%d", time.localtime(end_ts))
            else:
                if input_dict.get("history_range_days") != 'Unknown':
                    structured_start = time.strptime(input_dict.get("start_date"), "%Y-%m-%d")
                    end_ts = time.mktime(structured_start) + 24 * 3600 * (int(input_dict["history_range_days"]) - 1)
                    last_date_ts = time.localtime(time.time()) - 24 * 3600
                    input_dict["end_date"] = time.strftime("%Y-%m-%d", time.localtime(end_ts))

                else:
                    input_dict["target_date"] = DEFAULT_TARGET_DATE
                    structured_target = time.strptime(input_dict.get("target_date"), "%Y-%m-%d")
                    end_ts = time.mktime(structured_target) - 24 * 3600
                    input_dict["end_date"] = time.strftime("%Y-%m-%d", time.localtime(end_ts))

        elif input_dict.get("start_date") == 'Unknown':
            if input_dict.get("history_range_days") == 'Unknown':
                input_dict["history_range_days"] = DEFAULT_HISTORY_DAYS
            structured_end = time.strptime(input_dict.get("end_date"), "%Y-%m-%d")
            start_ts = time.mktime(structured_end) - 24 * 3600 * (int(input_dict["history_range_days"]) - 1)
            input_dict["start_date"] = time.strftime("%Y-%m-%d", time.localtime(start_ts))

        # print(input_dict)
        # 判断给定的历史数据窗口是否包含今天或未来日期， 若包含，则预测今天的退服概率
        if input_dict.get("end_date") >= DEFAULT_TARGET_DATE:
            print("指定的历史数据范围包含了未来日期，为您预测今天的退服概率，请检查指定的历史时间窗口后重试！")
            structured_target = time.strptime(input_dict.get("target_date"), "%Y-%m-%d")
            end_ts = time.mktime(structured_target) - 24 * 3600
            input_dict["end_date"] = time.strftime("%Y-%m-%d", time.localtime(end_ts))

        return input_dict

    def generate_json(self, text: str) -> dict:
        """
        Use this tool to generate a dictionary from input string according to the given prompt.
        Input must contain [target date], [the ID of base station].
        :param text: string
        :return: a dictionary that summarize input string.
        """
        print(DEFAULT_TARGET_DATE)
        target_date_schema = ResponseSchema(name="target_date",
                                            # description="The date of target day to be predicted, formatted as %Y-%m-%d, if not mentioned, set [{}].".format(DEFAULT_TARGET_DATE))
                                            description="""
                                            这是退服预测的预测目标日期，是一串格式为[%Y-%m-%d]的字符串，例如[2022-11-13]
                                            如果用户的输入中，提到[今天]或[未来]或未提及预测目标日期，则取值为{}
                                                        
                                            """
                                            .format(DEFAULT_TARGET_DATE))
        # "For example, from [预测2022年11月13日的基站退服概率], target_date=2022-11-13."
        node_name_schema = ResponseSchema(name="node_name",
                                          description="这是退服预测的预测目标基站名称。是一串包含中文、数字和英文字母以及符号的字符串。只能从输入的文本中原样提取，不能增加任何字符，不能替换任何字符，不能删减任何字符。只能原样提取不可做任何更改。"
                                                      "例如 [沈阳大东区上园路7号-上园路13-1号051178TDD-HLY]就是一个合法的基站名称。"
                                                      "如果用户输入中未提到基站名称，就置为 [Unknown].")

        response_schemas = [target_date_schema, node_name_schema]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        # print("format_instructions:\n", format_instructions)

        prompt_template = """
        For the following text in braces, 
            1. If given a chinese text, translate it into English for better understanding. 
            2. Extract following information in double quotes according to the given format instruction, but make sure the language of the extracted field values be consistent with the original text.
            3. Format the output as JSON with keys: [target_date, node_name]
        text: 
            {text}
            If given a chinese text, translate it into English for better understanding. 
            But make sure the language of the extracted field values be consistent with the original text

        information to extract:
            "
            target_date: The date of day to be predicted, formatted as %Y-%m-%d, if not mentioned, set as [{default_target_date}].
            node_name: Name of base station, if not mentioned, set [Unknown].
            "
        format instruction: {format_instructions}
        """

        prompt = ChatPromptTemplate.from_template(prompt_template)
        # print("prompt_template:\n", prompt, '\n', prompt.dict())

        # llm initialization
        # llm = OpenAI(openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
        llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)
        messages = prompt.format_messages(text=text, format_instructions=format_instructions,
                                          default_target_date=DEFAULT_TARGET_DATE,
                                          default_history_range=DEFAULT_HISTORY_DAYS)
        ai_output = llm.predict_messages(messages)
        json_str = ai_output.content.replace('\\', '\\\\')
        # print(json_str)
        output_dict = output_parser.parse(json_str)
        return output_dict

    def check_info(self, extracted: dict):
        check_name = False
        re_input_cnt = 0
        while not check_name:
            if re_input_cnt > MAX_REINPUT_CNT:
                raise Exception("超出核对次数限制，请核对好您的信息后重试！")
            if extracted["node_name"] == "Unknown":
                extracted["node_name"] = input("未识别到可用的基站名称，请重新输入：node_name=")
            print("提取到基站名称为：{}，请确认该名称是否正确...".format(
                extracted["node_name"]))
            flag = input("正确无误请输入y，错误请输入n，输入后按回车确认:")
            if flag in ['y', 'Y', "yes"]:
                check_name = True
            elif flag in ['n', 'N', "no"]:
                extracted["node_name"] = input("请输入正确的基站名称，请重新输入：node_name=")
            else:
                print("您的输入有误。正确无误请输y，错误请输入n...重新为您核对信息...")
            re_input_cnt += 1
        if extracted["node_name"] == "Unknown":
            raise Exception("未识别到可用的基站名称, 请核对好您的信息后重试！")

        check_date = False
        re_input_cnt = 0
        while not check_date:
            if re_input_cnt > MAX_REINPUT_CNT:
                raise Exception("超出核对次数限制，请核对好您的信息后重试！")
            if extracted["target_date"] == "Unknown":
                extracted["node_name"] = input("未识别到目标预测日期，请按照%Y-%m-%d格式重新输入：target_date=")
            print("提取到目标预测日期为：{}，请确认该目标日期是否正确...".format(
                extracted["target_date"]))
            flag = input("正确无误请输入y，错误请输入n，输入后按回车确认:")
            if flag in ['y', 'Y', "yes"]:
                check_date = True
            elif flag in ['n', 'N', "no"]:
                extracted["target_date"] = input("请输入正确的目标预测日期，请按照%Y-%m-%d格式重新输入：target_date=")
            else:
                print("您的输入有误。正确无误请输y，错误请输入n...重新为您核对信息...")
            re_input_cnt += 1
        if extracted["target_date"] == "Unknown":
            raise Exception("未识别到可用的目标预测日期, 请核对好您的信息后重试！")

        return extracted

    def _run(self, input_text: str):
        print("\n------IN OPS PREDICT TOOL------\n")
        print(
            """AI input:
            {}
            """.format(input_text)
        )

        extracted_info = self.generate_json(input_text)

        # checked_info = self.check_info(extracted_info)
        checked_info = extracted_info
        # alarm_file_folder = checked_info["alarm_file_folder"].strip()
        target_date = checked_info["target_date"].strip()
        node_name = checked_info["node_name"].strip()

        data = {
            "alarm_file_folder": PREDICT_ALARM_FILE_FOLDER,
            "target_date": target_date,
            "history_range_days": DEFAULT_HISTORY_DAYS,
            "start_date": "Unknown",
            "end_date": "Unknown",
            "province": "Unknown",
            "city": "Unknown",
            "vender": "Unknown",
            "nettype": "Unknown",
            "enodebid": "Unknown",
            "node_name": node_name
        }
        data = self.check_date(data)

        print("\nSTEP 1: generate the JSON body:\n", data)

        print("\nSTEP 2: send a POST request:\n\turl:{}\n".format(OPS_PREDICT_API_URL))
        print("\npredicting....")
        time_st = "prediction start at {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_st)
        response = requests.post(OPS_PREDICT_API_URL, json=data)
        time_end = "API调用结束时间：{}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_end)

        result = response.json()
        print("GET RESPONSE:\n", result)
        # print("retirement rate =", result["result"]['retirement_rate'])
        retirement_rate = result["result"]['retirement_rate']
        station_info = result["result"]['station_info']
        # alarm_list = station_info['alarm_info'][2:-3].split('], [')
        alarm_list = station_info['alarm_info']
        alarm_info = f"{node_name}基站在 {data['start_date']} 至 {data['end_date']} 期间的告警记录为：\n"
        for i, alarm in enumerate(alarm_list):
            # info_list = alarm.split(",")
            alarm_info += f"第{i + 1}次告警开始于{alarm[0]}, 告警名称为[{alarm[1]}].\n"

        output = (
            "分析预测结果如下:名为 {name} 的基站 未来一周的退服概率为{rate}。\n\t该基站ID为 {id} 号，位于{province}省{city}市，由{vendor}提供的{net_type}网络。\n\t读取预处理该基站 {start_date} 至 {end_date} 告警数据，启动基站退服预测能力调用。\n{alarm_info}"
                .format(
                id=station_info["id"], name=node_name, start_date=data["start_date"], end_date=data["end_date"],
                province=station_info["province"], city=station_info["city"], vendor=station_info["vendor"],
                net_type=station_info["net_type"], rate=retirement_rate, alarm_info=alarm_info
            ))

        log_api = f"调用--用户故障预防API--退服预测能力\n{time_st}\n{time_end}访问的url是:\t{OPS_PREDICT_API_URL}\n\n" + output
        log_api = log_api.replace('\t', '&nbsp;' * 4)
        log_api = log_api.replace('\n', '<br>')

        # return result["result"]
        return log_api

    def _arun(self, params):
        raise NotImplementedError("暂不支持异步")
