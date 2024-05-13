# -*- coding: utf-8 -*-
from langchain.utilities.sql_database import SQLDatabase
import copy
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from paramslist import DATABASE_URL, DATABASE_URL_X, OPENAI_API_KEY_X, OPENAI_API_BASE_X, OPENAI_KEY2, OPENAI_API_KEY_X2,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME

pg_uri = DATABASE_URL_X
db = SQLDatabase.from_uri(pg_uri)


class Status_1_solutionChain:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW, model_name = MODEL_NAME, temperature=0)
        self.memory = ConversationBufferMemory(return_messages=True)

        # template = """
        # You are a helpful assistant to return results based on user input.
        # 1.This type of problem generates postgres SQL query statements for users.
        # If the question in user's input like that:请查询隐患基站XXX相应告警情况？or 隐患基站XXX相关的告警有什么？or 隐患基站XXX近期发生过哪些告警？
        # then you need to generate postgresql queries based on the action entered by the user.Only returned postgresSQL query statements are returned because I need to query directly to the database.
        #
        # 2.The following question queries the data stored in memory and returns the corresponding result directly to the user, not sql.
        # If the question in the user's input  like that: 针对该隐患基站的告警如何处理？ or 请生成该隐患基站处理方案 or 请告诉我如何处理该隐患基站？
        # Return the result to the user in the following example format by querying the dictionary in the content of AIMessage saved in the dialog,and then will output information corresponding to the field 'attenfrequencyalarm' and output format example:"处理方案建议: XXXX"
        # """
        #         template = """
        # You are a helpful assistant to return results based on user input.
        # if the question in human input like that:请查询隐患基站XXX相应告警情况？or 隐患基站XXX相关的告警有什么？or 隐患基站XXX近期发生过哪些告警？
        # then you need to generate postgresql queries based on the action entered by the user.Only returned postgresSQL query statements are returned because I need to query directly to the database.
        #  else if the question in the user input  like that: 针对该隐患基站的告警如何处理？or 请生成该隐患基站处理方案 or 请告诉我如何处理该隐患基站？
        # then will output information corresponding to the field 'attenfrequencyalarm' and output format example:"处理方案建议: XXXX"
        # """
        template = """
        你是一个根据用户输入不同返回针对性信息的助手。
        1.假如用户输入中的question是如下示例：请查询隐患基站XXX相应告警情况？or 隐患基站XXX相关的告警有什么？or 隐患基站XXX近期发生过哪些告警？
        那么根据用户输入中的action对应的表名，字段信息，生成postgresql，只返回postgresql，用于直接去数据库进行查询，不要带有文字。
        示例：
        用户输入:
            question:请查询隐患基站丹东宽甸县联通海王府酒店150873FDD-HLH相应告警情况？action:查询re_result表，字段NAME = '丹东宽甸县联通海王府酒店150873FDD-HLH';
        助手输出：
            SELECT * FROM re_result WHERE NAME = '丹东宽甸县联通海王府酒店150873FDD-HLH';
        
        2.假如用户输入中的question是如下示例：针对该隐患基站的告警如何处理？or 请生成该隐患基站处理方案 or 请告诉我如何处理该隐患基站？
        请根据本对话保存的历史信息中，找到'alarmmeasure'对应的内容返回给用户，如果未找到请重新检查自己的历史对话，里面HumanMessage存的content是SQL语句，AIMessage存入的content就包含这个参数。如果找到多条信息，则合并返回，返回的示例如下：
        ‘处理方案建议: XXXX’ 
        示例：
        用户输入:question:针对该隐患基站的告警如何处理？action:触发查询历史信息回答对应问题。
        助手输出：
            处理方案建议：XXX
        
        请以示例的格式输出最终结果，不要添加其他文字。例如，保存到历史信息中找到 'alarmmeasure': '1、检查本端和对端的配置是否正确； 2、检查是否存在单板硬件故障； 3、检查是否存在底层链路故障； 4、检查证书是否失效；'
        则应输出：
            处理方案建议：1、检查本端和对端的配置是否正确； 
                        2、检查是否存在单板硬件故障； 
                        3、检查是否存在底层链路故障； 
                        4、检查证书是否失效；
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self, input: str):
        output = self.conversation.predict(input=input)
        print("STEP3=====converstation output:\n", output)
        history3 = self.conversation.memory.load_memory_variables({})
        print('history',history3)
        return output




def out_result(data):
    # data = [dict(zip(columns, row)) for row in rows]
    column_names = {
        "alarmmeasure": "告警处理措施",
        "attenfrequencyalarm": "重点关注影响业务告警发生频次",
    }
    transformed_data = []
    for item in data:
        transformed_item = {}
        for key, value in item.items():
            if key in column_names:
                transformed_item[column_names[key]] = value
        transformed_data.append(transformed_item)

    if transformed_data:
        result = "查询该基站近期告警情况：<br>"
        for item in transformed_data:
            print(item)
            result += item['重点关注影响业务告警发生频次'] + '<br>'
    else:
        result = '未查询到相关信息'
    return result


def result_record(reords):
    new_records = []
    for rec in reords:
        dict_rec = {}
        dict_rec['alarmmeasure'] = rec[30]
        dict_rec['attenfrequencyalarm'] = rec[5]
        new_records.append(copy.deepcopy(dict_rec))
    return new_records


def get_1_result(sql, conversation):
    query_result = db.run_no_str(sql)
    print('\n数据库查询得到的所有数据\n',query_result)
    if (isinstance(query_result, list) and len(query_result) > 0):
        resu_sql = result_record(query_result)
        print('\n保存到memory中的列表信息\n',resu_sql)
        conversation.memory.save_context({"input": sql}, {"output": str(resu_sql)})
    else:
        resu_sql = []
    resu_sql = out_result(resu_sql)

    print('\n最终传给前端的信息\n',resu_sql)
    return resu_sql


# if  __name__ == '__main__':
#     from solution_5 import extract_sql
#     text = "question:隐患丹东东港市英豪小区154116FDD-HLH相关的告警有什么？action:查询re_result表，字段NAME = '丹东东港市英豪小区154116FDD-HLH';"
#     q2 = "question: 请生成该隐患基站处理方案？action:触发查询历史信息回答对应问题。"
#     conversation = Status_1_solutionChain()
#     while True:
#         input_data = input('请输入问题：')
#         res = conversation.predict(input = input_data)
#         print(res)
#         sql = extract_sql(res)
#         print(sql)
#     # status_list.append(status)
#         if sql.startswith("SELECT"):
#             result_return = get_1_result(sql, conversation)
#         else:
#             result_return = sql
#         print('\n最终结果',result_return)
        #



