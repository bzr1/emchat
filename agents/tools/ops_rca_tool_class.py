import time
import requests
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate

from langchain.tools import BaseTool
from paramslist import MAX_REINPUT_CNT, OPS_RCA_API_URL, RCA_ALARM_FILE_PATH, RCA_ORDER_FILE_PATH

class OpsRcaTool(BaseTool):
    name = "ops_rca_tool"
    return_direct = True
    description = """
    此工具可以进行基站告警根因分析。
    根据用户输入的信息，提取故障工单的工单号（order_name），对故障告警进行归因，返回告警的原因。
    只能从用户输入的文本中原样提取工单号，不要自行删减字符。
    工具输入是用户输入的待分析的故障工单（order）名称， 由字符和数字组成， 例如[ID-151-20210801-00010]。若未识别到, 置为 [Unknown].
    工具输出工单故障告警的原因。
    请将工具的输出直接返回给用户以免损失信息。
    """
    # 输入示例：target_date=[target_date or ‘Unknown’], node_name=[node_name or ‘Unknown’]。
    # 工具的输入是一段文本字符串 input_text，其中包含的信息有：1. target_date，是预测目标的日期; 2.node_name，是预测目标基站名称，为一串中文+符号+大写英文字母组成的字符串；

    def __init__(self):
        super().__init__()

    def check_info(self, extracted: dict):
        check_name = False
        re_input_cnt = 0
        while not check_name:
            if re_input_cnt > MAX_REINPUT_CNT:
                raise Exception("超出核对次数限制，请核对好您的信息后重试！")
            if extracted["order_name"] == "Unknown":
                extracted["order_name"] = input("未识别到可用的故障工单名称，请重新输入：order_name=")
            print("提取到故障工单名称为：{}，请确认该名称是否正确...".format(
                extracted["order_name"]))
            flag = input("正确无误请输入y，错误请输入n，输入后按回车确认:")
            if flag in ['y', 'Y', "yes"]:
                check_name = True
            elif flag in ['n', 'N', "no"]:
                extracted["order_name"] = input("请输入正确的故障工单名称，请重新输入：order_name=")
            else:
                print("您的输入有误。正确无误请输y，错误请输入n...重新为您核对信息...")
            re_input_cnt += 1
        if extracted["order_name"] == "Unknown":
            raise Exception("未识别到可用的故障名称, 请核对好您的信息后重试！")
        return extracted

    def _run(self, order_name: str):
        print("\n------IN OPS RCA TOOL------\n")
        print(
            """AI input:
            order_name: {}
            """.format(order_name)
        )

        data = {
            "alarm_file_path": RCA_ALARM_FILE_PATH,
            "order_file_path": RCA_ORDER_FILE_PATH,
            "order_name": order_name
        }
        # checked_info = self.check_info(data)
        checked_info = data
        # alarm_file_folder = checked_info["alarm_file_folder"].strip()

        order_name = checked_info["order_name"].strip()

        print("\nSTEP 1: generate the JSON body:\n", checked_info)

        print("\nSTEP 2: send a POST request:\n\turl:{}\n\tpost body:{}".format(OPS_RCA_API_URL, checked_info))
        print("\npredicting....")
        time_st = "API调用开始时间：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_st)
        response = requests.post(OPS_RCA_API_URL, json=data)
        # result ={'code': 200, 'msg': 'success', 'result': '无线及设备原因-GPS'}
        # response.raise_for_status()
        time_end = "API调用结束时间：{}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_end)

        result = response.json()
        print("GET RESPONSE:\n", result)
        # print("retirement rate =", result["result"]['retirement_rate'])
        reason = result["result"]
        output = "根因分析结果如下:名为 {name} 的故障工单，告警原因为{reason}。".format(name=order_name, reason=reason)
        log_api = f"调用--故障诊断与定位API--根因分析能力\n{time_st}\n{time_end}访问的url是:\t{OPS_RCA_API_URL}\n\n" + output
        log_api = log_api.replace('\t', '&nbsp;' * 4)
        log_api = log_api.replace('\n', '<br>')
        return log_api

    def _arun(self, params):
        raise NotImplementedError("暂不支持异步")
