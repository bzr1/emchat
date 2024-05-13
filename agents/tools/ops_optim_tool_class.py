import datetime
import time
import requests
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate

from langchain.tools import BaseTool
from paramslist import DEFAULT_TARGET_DATE, DEFAULT_HISTORY_DAYS, PERFORMANCE_OPTIM_API_URL, MAX_REINPUT_CNT
from paramslist import OPENAI_API_KEY_QW, OPENAI_API_BASE_QW, MODEL_NAME


class OpsOptimTool(BaseTool):
    name = "ops_optim_tool"
    return_direct = True
    description = """
    此工具 评估分析 基站/小区的 网络状态。
    工具输入是一段文本字符串，[Action Input = 用户输入]，请将用户输入 原样传入 工具，以免损失信息。
    工具输出小区信息和小区存在的问题列表：小区信息中包含小区的名字、所属场景和运行状态；问题列表中，每行包含问题类型和相关参数的取值。
    请将工具的输出直接返回给用户以免损失信息。
    """
    # 输入示例：target_date=[target_date or ‘Unknown’], node_name=[node_name or ‘Unknown’]。
    # 工具的输入是一段文本字符串 input_text，其中包含的信息有：1. target_date，是预测目标的日期; 2.node_name，是预测目标基站名称，为一串中文+符号+大写英文字母组成的字符串；


    def generate_json(self, text: str) -> dict:
        """
        Use this tool to generate a dictionary from input string according to the given prompt.
        Input must contain [target date], [the ID of base station].
        :param text: string
        :return: a dictionary that summarize input string.
        """
        residence_name_schema = ResponseSchema(name="residence_name",
                                               description="""小区或基站的名称， 由中文字符、英文大写字母、符号'-'和数字组成。
                                                   例如，从 [长沙中南工大升华大楼-H5H-D59002490534PT-2611], 能提取到order_name="长沙中南工大升华大楼-H5H-D59002490534PT-2611".
                                                   若未识别到, 置为 [Unknown]."
                                                   """)
        target_date_schema = ResponseSchema(name="target_date",
                                            description="""
                                                指定的日期，需要分析小区或基站在那一天的网络状态。
                                                请转换为[%Y%m%d]格式。
                                                例如, 根据 [请分析小区在2023年11月10日的网络状态], target_date=“20231110"
                                                若用户提到了 ["未来"] or ["今天"] or ["future"] or ["today"], 设置为 [{}]; 若用户没提到目标日期，设为 [{}].
                                                """
                                            .format(datetime.datetime.now().strftime("%Y%m%d"),
                                                    datetime.datetime.now().strftime("%Y%m%d"))
                                            )
        response_schemas = [residence_name_schema, target_date_schema]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        # print("format_instructions:\n", format_instructions)
        prompt_template = """
                           对于中括号内的文本text, 
                               1. 根据下面的格式指示（format_instructions）提取字段, 提取到的字段要与原文本中的保持一致
                               2. Format the output as JSON with keys: [action, residence_name, target_date]
                           text: 
                               {text}

                           需要提取的信息:
                               "
                               action: 这是用户需要你进行的操作，请根据你的理解设置为[status or suggestion or chat]
                               residence_name: 小区或基站名称， 若未提及，置为 [Unknown].
                               target_date：指定的日期，请转换为[%Y%m%d]格式。
                               "
                           format instruction: {format_instructions}
                           """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        # print("prompt_template:\n", prompt, '\n', prompt.dict())

        # llm initialization
        # llm = OpenAI(openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
        llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)
        messages = prompt.format_messages(text=text, format_instructions=format_instructions)
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
            if extracted["residence_name"] == "Unknown":
                extracted["residence_name"] = input("未识别到可用的小区或基站名称，请重新输入：residence_name=")
            print("提取到小区或基站名称为：{}，请确认该名称是否正确...".format(
                extracted["residence_name"]))
            flag = input("正确无误请输入y，错误请输入n，输入后按回车确认:")
            if flag in ['y', 'Y', "yes"]:
                check_name = True
            elif flag in ['n', 'N', "no"]:
                extracted["residence_name"] = input("请输入正确的小区或基站名称，请重新输入：residence_name=")
            else:
                print("您的输入有误。正确无误请输y，错误请输入n...重新为您核对信息...")
            re_input_cnt += 1
        if extracted["residence_name"] == "Unknown":
            raise Exception("未识别到可用的小区或基站名称, 请核对好您的信息后重试！")

        check_date = False
        re_input_cnt = 0
        while not check_date:
            if re_input_cnt > MAX_REINPUT_CNT:
                raise Exception("超出核对次数限制，请核对好您的信息后重试！")
            if extracted["target_date"] == "Unknown":
                extracted["node_name"] = input("未识别到目标预测日期，请按照%Y%m%d格式重新输入：target_date=")
            print("提取到目标预测日期为：{}，请确认该目标日期是否正确...".format(
                extracted["target_date"]))
            flag = input("正确无误请输入y，错误请输入n，输入后按回车确认:")
            if flag in ['y', 'Y', "yes"]:
                check_date = True
            elif flag in ['n', 'N', "no"]:
                extracted["target_date"] = input("请输入正确的目标预测日期，请按照%Y%m%d格式重新输入：target_date=")
            else:
                print("您的输入有误。正确无误请输y，错误请输入n...重新为您核对信息...")
            re_input_cnt += 1
        if extracted["target_date"] == "Unknown":
            raise Exception("未识别到可用的目标预测日期, 请核对好您的信息后重试！")
        return extracted

    def _run(self, input_text: str):
        print("\n------IN OPS OPTIM TOOL------\n")
        print(
            """AI input:
            {}
            """.format(input_text)
        )
        extracted = self.generate_json(input_text)
        # print(extracted)
        # checked_info = self.check_info(extracted)
        checked_info = extracted
        residence_name = checked_info["residence_name"].strip()
        target_date = checked_info["target_date"].strip()

        data = {
            "target_date": target_date,
            "residence_name": residence_name
        }

        print("\nSTEP 1: generate the JSON body:\n", data)

        print("\nSTEP 2: send a POST request:\n\turl:{}\n\tpost body:{}".format(PERFORMANCE_OPTIM_API_URL, data))
        print("\npredicting....")
        time_st = "API调用开始时间：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_st)
        response = requests.post(PERFORMANCE_OPTIM_API_URL, json=data)
        time_end = "API调用结束时间：{}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_end)

        # print(response)

        result = response.json()
        print("GET RESPONSE:\n", result)
        # print("retirement rate =", result["result"]['retirement_rate'])
        residence_info_list = result["result"]["residence_info"].split('|')
        status = result["result"]["status_info"]

        residence_info = f"[{residence_name}]基站属于{residence_info_list[-2]}的{residence_info_list[-3]}场景，运行状态为{residence_info_list[-1]}。"
        status_info = f"该基站在{target_date}这天的网络状态存在如下问题：\n"
        for i, info in enumerate(status):
            info_list = info.split("|")
            status_info += f"{i + 1}、\t小区存在[{info_list[2]}]问题，问题指标是：{info_list[5]}。\n"

        output = "网络状态分析结果如下: \n{residence_info}\n{status_info}".format(residence_info=residence_info,
                                                                                  status_info=status_info)
        log_api = f"调用--网络性能优化API--网络优化能力\n{time_st}\n{time_end}访问的url是:\t{PERFORMANCE_OPTIM_API_URL}\n\n" + output
        log_api = log_api.replace('\t', '&nbsp;' * 4)
        log_api = log_api.replace('\n', '<br>')

        return log_api

    def _arun(self, params):
        raise NotImplementedError("暂不支持异步")
