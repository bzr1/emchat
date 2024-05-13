# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
# import psycopg2
import openai
import certifi
import requests
import re
from functions.chroma_doc import embed_start
from functions.solution_0 import get_0_result, Status_0_solutionChain, Status_chatChain
from functions.solution_1 import get_1_result, Status_1_solutionChain
from functions.solution_3 import get_3_result, Status_3_solutionChain
from functions.solution_3 import extract_sql_3
# from functions.solution_2 import OpsPredictChain
# from functions.solution_4 import OpsRcaChain
from functions.solution_5 import get_5_result, Status_5_solutionChain, extract_sql
# from functions.solution_6 import PerformanceOptimChain
# from functions.solution_7 import TrafficPredictChain
from functions.solution_8 import Status_8_solutionChain, get_8_result
from agents.tools_agent import init_agent
from paramslist import PREFIX, STATUS_API

app = Flask(__name__)
# app.config['PORT'] = 9003
status_list = [-1]

# status_-1解决
conversation_chat = Status_chatChain()

# status_0解决
conversation_0 = Status_0_solutionChain()

# status_1解决
conversation_1 = Status_1_solutionChain()

# status_2解决
# conversation_2 = OpsPredictChain()

# status_3解决
conversation_3 = Status_3_solutionChain()

# status_4解决
# conversation_4 = OpsRcaChain()

conversation_5 = Status_5_solutionChain()

# status_6解决
# conversation_6 = PerformanceOptimChain()

# status_7解决
# conversation_7 = TrafficPredictChain()

# status_8解决
conversation_8 = Status_8_solutionChain()

# STATUS_API解决
tools_agent = init_agent()
#
# from langchain.chat_models import ChatOpenAI
#
# from langchain.agents import initialize_agent, AgentType, ConversationalAgent, ZeroShotAgent, AgentExecutor
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import StringPromptTemplate
# from langchain.tools import Tool, BaseTool
#
# from paramslist import OPENAI_API_KEY, OPENAI_API_BASE, PREDICT_ALARM_FILE_FOLDER
# from paramslist import OPENAI_API_KEY_QW, OPENAI_API_BASE_QW, MODEL_NAME
# from agents.tools.ops_predict_tool_class import OpsPredictTool
# from agents.tools.ops_optim_tool_class import OpsOptimTool
# from agents.tools.ops_rca_tool_class import OpsRcaTool
#
# from agents.custom_output_parser import CustomOutputParser
# from agents.tools_agent import AGENT_TMPL, CustomPromptTemplate
#
#
# llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)
# tools = [
#     OpsPredictTool(),
#     OpsOptimTool(),
#     OpsRcaTool()
# ]
# prompt = CustomPromptTemplate(
#     template=AGENT_TMPL,
#     tools=tools,
#     input_variables=["chat_history", "input", "intermediate_steps"],
#     tool_names = [tool.name for tool in tools]
# )
# output_parser = CustomOutputParser()
# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
# agent = ConversationalAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True, handle_parsing_errors=True,
#                                                output_parser=output_parser, stop=["\nObservation:"])
# agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors=True)

def check_empty_list(lst):
    if not lst:  # 列表为空
        return "未查询到结果"
    else:  # 列表不为空
        return lst


def fin_ret(status,question,actions,id_doc):
    result_return = ''
    try:
        if status == -1:  # 表示未匹配到准确信息
            print("\nSTEP2=====status:\n", status)
            print("\n进入专业知识问答或提建议对话\n")
            result_return = conversation_chat.predict(input=question)
            status_list.append(status)
            # return result

        elif status == 0:  # 表示匹配到0类问题
            print("\nSTEP2=====status:\n", status)
            que_action = 'question:' + question + actions
            print(que_action)
            sql = conversation_0.predict(input=que_action)
            sql = extract_sql(sql)
            print('0000', sql)
            result_return = get_0_result(sql)
            status_list.append(status)
            # return restult

        elif status == 1:  # 表示匹配到1类问题
            print("STEP2=====status:\n", status)

            que_action = 'question:' + question + actions
            print(que_action)
            sql = conversation_1.predict(input=que_action)
            sql = extract_sql(sql)

            print("111111111回答", sql)
            status_list.append(status)
            if sql.startswith("SELECT"):
                result_return = get_1_result(sql, conversation_1)
                # return result_1
            else:
                result_return = sql

        elif status == 3:  # 表示匹配到3类问题
            print("STEP2=====status:\n", status)
            # if status_list[-1] == '3':
            #     que_action = question
            # else:
            #     que_action = 'question:' + question + actions
            que_action = 'question:' + question + actions
            print(que_action)
            sql = conversation_3.predict(input=que_action,id_doc=id_doc)
            sql = extract_sql_3(sql)
            print(sql)
            if not sql.endswith(";"):
                sql = sql + ";"
                print(sql)
            status_list.append(status)
            if sql.startswith("SELECT"):
                result_return = get_3_result(sql, conversation_3)
            else:
                result_return = sql

        elif status == 5:  # 表示匹配到1类问题
            que_action = 'question:' + question + actions
            print(que_action)
            # conversation.predict('key:' + question + actions).content.strip()
            # sql = conversation_5.predict(input=que_action)
            sql = conversation_5.predict(input=que_action).content.strip()
            sql = extract_sql(sql)
            print("回答", sql)
            status_list.append(status)
            if sql.startswith("SELECT"):
                result_return = get_5_result(sql, conversation_5)
                # return result_1
            else:
                result_return = sql

        elif status == 8:  # 表示匹配到8类问题
            que_action = 'question:' + question + actions
            print(que_action)
            sql = conversation_8.predict(input=que_action)
            sql = extract_sql(sql)
            print("回答", sql)
            status_list.append(status)
            if sql.startswith("SELECT"):
                result_return = get_8_result(sql, conversation_8)
                # return result_1
            else:
                result_return = sql

        elif status in STATUS_API:  # 表示匹配到调用api问题
            # que_action = 'question' + question
            status_list.append(status)
            result_return = tools_agent.run(input=question, chat_history='')
            if result_return[0] == PREFIX: #流量预测工具返回的结果在前端中由曲线图展示，因此返回信息中包含记号PREFIX
                conversation_chat.memory.save_context({"input": question}, {"output": result_return.split(PREFIX)[-1]})
                print('agent调用工具获取到的返回结果', result_return.split(PREFIX)[-1])
            else:
                conversation_chat.memory.save_context({"input": question}, {"output": result_return})
                print('agent调用工具获取到的返回结果', result_return)

        # elif status == 2:  # 表示匹配到2类问题
        #     # que_action = 'question' + question
        #
        #     result_return = conversation_2.predict(question)
        #     status_list.append(status)
        #     print('调用退服预测获取到的返回结果', result_return)
        #
        # elif status == 6:  # 表示匹配到6类问题
        #     # que_action = 'question' + question
        #
        #     result_return = conversation_6.predict(question)
        #     status_list.append(status)
        #     print('调用网络优化获取到的返回结果', result_return)

        # elif status == 7:  # 表示匹配到7类问题
        #     # que_action = 'question' + question
        #     result_return = conversation_7.predict(question)
        #     # result_return = "!时间戳!预测到小区[A-JZ-WLMQKFQGAJ-HLW-1]在未来12小时的下行流量序列（Kbyte）为：\n[5182934.3785, 3228616.3681, 1329598.065, 1708573.7464, 2243463.1721, 3409517.0984, 1429897.6617, 2359660.9562, 1305154.7343, 2449440.1161, 1960108.8048, 1924056.2132]，未来序列的均值为2377585.1096，方差为1138053487314.6917。\n该小区最近12小时的历史下行流量序列（Kbyte）为:\n[5362349.345, 3161628.268, 2933135.176, 1939198.732, 1229553.556, 1100514.812, 914485.277, 618432.819, 809042.13, 1458983.593, 1320808.831, 1638288.507]，过去这12小时流量序列的均值为1873868.4205，方差为1677603996874.6067。"
        #     status_list.append(status)
        #     if result_return[0] == PREFIX:
        #         print('调用流量预测获取到的返回结果', result_return.split(PREFIX)[-1])
        #     else:
        #         print('调用流量预测获取到的返回结果', result_return)
        else:  # 表示未匹配到准确信息
            print('所有情况以外的conversation\n', status)
            result_return = conversation_chat.predict(input=question)
            status_list.append(status)
            result_return = result_return
            # return result

        return jsonify(check_empty_list(result_return))
    except Exception as e:
        # 处理异常情况
        print(e)
        res = '未查询到信息'
        return jsonify(res)



@app.route('/query', methods=['POST'])
def handle_question():

    question = request.json['question']
    print("前端传入question：", question)

    status, actions,id_doc = embed_start(question=question)
    print("\nemd后获取到的status,actions\n", status, actions, "\nstatus类型", type(status))

    return fin_ret(status,question,actions,id_doc)


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=9003)
    app.run(host='0.0.0.0', port=9002)

    # print("D:/vmware_data/docker_panzhi/docker_app/app/")
    # app.run()


