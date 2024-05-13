import time
import requests
import numpy as np
from langchain.tools import BaseTool

from paramslist import MAX_REINPUT_CNT, TRAFFIC_PREDICT_API_URL, FORECAST_WINDOW, PREFIX, HISTORY_WINDOW


def analyze(sequence: list):
    return np.round(np.mean(sequence), 4), np.round(np.var(sequence), 4)

class TrafficPredictTool(BaseTool):
    name = "traffic_predict_tool"
    return_direct = True
    description = """
     此工具预测 基站/小区的 通信流量水平。
    工具输入待预测小区名称，由字符和数字组成，例如[A-JZ-WLMQKFQGAJ-HLW-1]。若未识别到, 置为 [Unknown].
    工具输出预测结果的流量序列。
    请将工具的输出直接返回给用户以免损失信息。
    """

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

    def _run(self, residence_name: str):
        print("\n------IN TRAFFIC PREDICT TOOL------\n")
        print(
            """AI input:
            residence_name: {}
            """.format(residence_name)
        )

        data = {
            "residence_name": residence_name
        }
        # checked_info = self.check_info(data)
        checked_info = data
        residence_name = checked_info["residence_name"].strip()

        print("\nSTEP 1: generate the JSON body:\n", data)

        print("\nSTEP 2: send a POST request:\n\turl:{}\n\tpost body:{}".format(TRAFFIC_PREDICT_API_URL, data))
        print("\npredicting....")
        time_st = "API调用开始时间：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_st)
        response = requests.post(TRAFFIC_PREDICT_API_URL, json=data)
        time_end = "API调用结束时间：{}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        print(time_end)

        # print(response)

        result = response.json()
        print("GET RESPONSE:\n", result)
        # print("retirement rate =", result["result"]['retirement_rate'])
        pred_info = result["result"]
        pred_y = pred_info["y"]
        history_y = pred_info["history_y"]
        time_series = pred_info["time_series"]

        mean_y, var_y = analyze(pred_y)
        mean_history_y, var_history_y = analyze(history_y)

        pred_str = f"预测到小区{residence_name}在未来{time_series[-FORECAST_WINDOW]}到{time_series[-1]}期间{FORECAST_WINDOW}个小时的下行流量序列（Kbyte）为：\n{pred_y}，未来12小时流量序列的均值为{mean_y}，方差为{var_y}。\n"
        ana_str = f"该小区过去{time_series[0]}到{time_series[HISTORY_WINDOW - 1]}的{HISTORY_WINDOW}个小时内的历史下行流量序列（Kbyte）为:\n{history_y}，过去这72小时流量序列的均值为{mean_history_y}，方差为{var_history_y}。"
        log_api = f"调用--用户需求预测API--流量预测能力\n{time_st}\n{time_end}访问的url是:\t{TRAFFIC_PREDICT_API_URL}\n\n"
        log_api = log_api.replace('\t', '&nbsp;' * 4)
        log_api = log_api.replace('\n', '<br>')
        # self.conversation.memory.save_context({"input": input_text}, {"output": pred_str + ana_str})
        return PREFIX + time_series[-FORECAST_WINDOW] + PREFIX + log_api + pred_str + ana_str


    def _arun(self, params):
        raise NotImplementedError("暂不支持异步")
