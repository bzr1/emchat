import time
import requests
import numpy as np

from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.llms.openai import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, \
    HumanMessagePromptTemplate

from paramslist import OPENAI_API_KEY, OPENAI_API_BASE, MAX_REINPUT_CNT, TRAFFIC_PREDICT_API_URL, HISTORY_WINDOW, FORECAST_WINDOW, PREFIX,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME


def generate_json(text: str) -> dict:
    """
    Use this tool to generate a dictionary from input string according to the given prompt.
    Input must contain [target date], [the name of base station].
    :param text: string
    :return: a dictionary that summarize input string.
    """
    action_schema = ResponseSchema(name="action", description="""
            If 用户输入要求你预测基站的未来流量水平: 置为 [predict].
            else if 只要用户提到[优化] or [建议] or [如何解决],例如[针对该小区的网络状态，请给出优化建议]：就置为 [suggestion].
            else, 其他情况下：置为 [chat]
            """)


    residence_name_schema = ResponseSchema(name="residence_name",
                                           description="""小区或基站的名称， 由中文字符、英文大写字母、符号'-'和数字组成。
                                           例如，从 [长沙中南工大升华大楼-H5H-D59002490534PT-2611], 能提取到order_name="长沙中南工大升华大楼-H5H-D59002490534PT-2611".
                                           若未识别到, 置为 [Unknown]."
                                           """)

    response_schemas = [action_schema, residence_name_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    # print("format_instructions:\n", format_instructions)
    prompt_template = """
                   对于中括号内的文本text, 
                       1. 根据下面的格式指示（format_instructions）提取字段, 提取到的字段要与原文本中的保持一致
                       2. Format the output as JSON with keys: [action, residence_name]
                   text: 
                       {text}

                   需要提取的信息:
                       "
                       action: 这是用户需要你进行的操作，请根据你的理解设置为[predict or suggestion or chat]
                       residence_name: 小区或基站名称， 若未提及，置为 [Unknown].
                       "
                   format instruction: {format_instructions}
                   """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    # print("prompt_template:\n", prompt, '\n', prompt.dict())

    # llm initialization
    # llm = OpenAI(openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME, openai_api_base=OPENAI_API_BASE_QW,
                     temperature=0)

    messages = prompt.format_messages(text=text, format_instructions=format_instructions)
    ai_output = llm.predict_messages(messages)
    json_str = ai_output.content.replace('\\', '\\\\')
    # print(json_str)
    output_dict = output_parser.parse(json_str)
    return output_dict


def check_info(extracted: dict):
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
    return extracted


def analyze(sequence: list):
    return np.round(np.mean(sequence), 4), np.round(np.var(sequence), 4)


class TrafficPredictChain:
    def __init__(self):
        self.openai_key = OPENAI_API_KEY
        self.openai_base = OPENAI_API_BASE
        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME, openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        # self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE, temperature=1)
        self.memory = ConversationBufferMemory(return_messages=True)

        template = """
        You are a helpful assistant to answer questions about communication Network base station and provide suggestions. 
        If user asked you to analyze or give suggestions based on the predicted traffic situation of a base station or a residence:
        1. check the chat history to find related records
        2. compare the predicted traffic level with recent historical traffic level
        2. answer the question according to records you found

        Do not reply any suggestions if you find nothing related to the base station,if so, just reply "NO RECORDS".
        """

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self, input_text: str):
        extracted = generate_json(input_text)
        print(extracted)
        if extracted["action"] == "predict":
            # checked_info = check_info(extracted)
            checked_info = extracted
            residence_name = checked_info["residence_name"].strip()

            data = {
                "name": residence_name
            }

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
            ana_str = f"该小区过去{time_series[0]}到{time_series[HISTORY_WINDOW-1]}的{HISTORY_WINDOW}个小时内的历史下行流量序列（Kbyte）为:\n{history_y}，过去这72小时流量序列的均值为{mean_history_y}，方差为{var_history_y}。"
            log_api = f"调用--用户需求预测API--流量预测能力\n{time_st}\n{time_end}访问的url是:\t{TRAFFIC_PREDICT_API_URL}\n\n"
            log_api = log_api.replace('\t', '&nbsp;' * 4)
            log_api = log_api.replace('\n', '<br>')

            self.conversation.memory.save_context({"input": input_text}, {"output": pred_str+ana_str})
            return PREFIX+time_series[-FORECAST_WINDOW]+PREFIX+log_api+pred_str+ana_str
        else:
            output = self.conversation.predict(input=input_text)
            # print(output)
            self.conversation.memory.save_context({"input": input_text}, {"output": output})
            # print(output["response"])
            return output


# text1 = "请预测小区A-JZ-WLMQKFQGAJ-HLW-1未来的下行流量水平"
# text2 = "针对该小区未来的流量状况，请给出优化建议"
# chain = TrafficPredictChain()
# chain.predict(text1)
# chain.predict(text2)

# epoch = 0
# while True:
#     try:
#         user_input = text1 if epoch == 0 else input("请输入您的问题：")
#         epoch += 1
#         ai_output = chain.predict(user_input)
        # output_response(response)
        # print(ai_output)
    # except KeyboardInterrupt:
    #     break