# -*- coding: utf-8 -*-
from langchain.utilities.sql_database import SQLDatabase
import copy
import re
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from paramslist import DATABASE_URL,DATABASE_URL_X,OPENAI_API_KEY_X3,OPENAI_API_BASE_X,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
pg_uri = DATABASE_URL_X
db = SQLDatabase.from_uri(pg_uri)




# class Status_5_solutionChain:
#     def __init__(self):
#         # self.openai_key = OPENAI_API_KEY_X3
#         # self.openai_base = OPENAI_API_BASE_X
#         self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
#                               openai_api_base=OPENAI_API_BASE_QW, temperature=0)
#         # self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_X3, openai_api_base=OPENAI_API_BASE_X, temperature=0)
#         # self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_X3,temperature=0)
#         self.memory = ConversationBufferMemory(return_messages=True)
#
#         template ="""
#            You are a helpful assistant to return results based on user input.
#         1.This type of problem generates postgres SQL query statements for users,don't with any other word.
#         If the question in user's input like that:请查询小区XXX在2023年11月10日的网络性能指标。
#         then you need to generate postgresql queries based on the action entered by the user.Please only returned postgresSQL query statements are returned because I need to query directly to the database.
#
#         """
#         prompt = ChatPromptTemplate.from_messages([
#             SystemMessagePromptTemplate.from_template(template),
#             MessagesPlaceholder(variable_name="history"),
#             HumanMessagePromptTemplate.from_template("{input}")
#         ])
#
#         self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)
#
#     def predict(self,input:str):
#         output = self.conversation.predict(input=input)
#         print('conversation_output\n'+output)
#         return output




class Status_5_solutionChain:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
                              openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        self.memory = ConversationBufferMemory(return_messages=True)

        template = """
        你是一个专业postgres SQL生成助手,不需要回答question的问题.

        用户的{input}中包含了question和action两部分,你无需在意question的内容,只需要根据action的内容生成准确的sql语句返回给用户.


        示例1：
        用户输入:question:查询小区郴州汝城南洞V92002512646PT-Z5H-2612在2023年11月10日的网络性能指标。action:查询history_index_hour_5g表，字段nr_cellname = '郴州汝城南洞V92002512646PT-Z5H-2612',字段date = '2023-11-10'; 
        助手输出:SELECT * FROM history_index_hour_5g WHERE nr_cellname = '郴州汝城南洞V92002512646PT-Z5H-2612' AND date = '2023-11-10';
        
        请严格按照例子中的格式返回sql语句给用户,不要带有其他文字.

        """
        template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=template),
                HumanMessagePromptTemplate.from_template("{input}"),  # "查询一下阜新彰武县五峰基站近期告警和处理情况"
            ]
        )

        self.chain = template | ChatOpenAI(
    model_name=MODEL_NAME,
    openai_api_key=OPENAI_API_KEY_QW,
    openai_api_base=OPENAI_API_BASE_QW, temperature=0,
    streaming=True)

    def predict(self, input: str):
        output = self.chain.invoke({"input":input})
        return output


def extract_sql(text):
    '''
    :param text:大模型返回的内容
    :return: 如果是SQL查询，则返回SQL，否则返回原内容
    '''
    sql_query_match1 = re.search(r'(?<=SELECT).*?(?=;)', text, re.DOTALL)
    sql_query_match2 = re.search(r'(?<=SELECT).*?(?=；)', text, re.DOTALL)
    # print(sql_query_match1,sql_query_match2)
    if sql_query_match1:
        sql_query = "SELECT " + sql_query_match1.group().strip() + ";"
        print('1',sql_query)
        return sql_query
    elif sql_query_match2:
        sql_query = "SELECT " + sql_query_match2.group().strip() + ";"
        print('2', sql_query)
        return sql_query
    else:
        return text


def result_record(reords):
    new_records = []
    for rec in reords:
        dict_rec = {}
        dict_rec['his001'] = rec[5]
        dict_rec['his002'] = rec[6]
        dict_rec['his010'] = rec[14]
        dict_rec['his011'] = rec[15]
        dict_rec['his012'] = rec[16]
        dict_rec['his013'] = rec[17]
        dict_rec['his016'] = rec[20]
        dict_rec['his017'] = rec[21]
        dict_rec['his031'] = rec[35]
        dict_rec['his032'] = rec[36]
        dict_rec['his033'] = rec[37]
        new_records.append(copy.deepcopy(dict_rec))
    return new_records



def out_result(data):
    # data = [dict(zip(columns, row)) for row in rows]
    column_names = {
        'his001': 'SN添加成功率',
        'his002': 'SN异常释放率',
        'his010': 'SA 切换成功率(SA)',
        'his011': '切换成功率(SA)',
        'his012': '接通率(SA)',
        'his013': '掉线率(SA)',
        'his016': '上行PRB平均利用率(SA)',
        'his017': '下行PRB平均利用率(SA)',
        'his031': '流量(SA)',
        'his032': 'gNB间Xn切换成功率(SA)',
        'his033': 'gNB间NG切换成功率(SA)'
    }
    transformed_data = []
    for item in data:
        transformed_item = {}
        for key, value in item.items():
            if key in column_names:
                transformed_item[column_names[key]] = value
        transformed_data.append(transformed_item)

    print(transformed_data)
    if transformed_data:
        result = "该小区常规性能指标查询结果如下：<br>"
        for item in transformed_data:
            print(item)
            for key,value in item.items():
                if value:
                    result += key + ':' + value + '; <br>'
    else:
        result = '未查询到相关信息'
    return result



def get_5_result(sql,conversation):
    query_result = db.run_no_str(sql)
    if (isinstance(query_result, list) and len(query_result) > 0):
        resu_sql = result_record(query_result)
        conversation.memory.save_context({"input": sql}, {"output": str(resu_sql)})
    else:
        resu_sql = []
    resu_sql = out_result(resu_sql)
    return resu_sql



# conversation = Status_5_solutionChain()
# ques_action = "question:请查询小区长沙东方红路与青山路交叉口-H5H-D59002490374PT-2612在2023年11月10日的网络性能指标。action:查询history_index_hour_5g表，字段nr_cellname = '长沙东方红路与青山路交叉口-H5H-D59002490374PT-2612',字段date = '2023-11-10';"
# text = """
#  生成的查询语句为：SELECT * FROM re_result WHERE NAME = '丹东宽甸县联通海王府酒店150873FDD-HLH'；
# """
# out_put = conversation.predict(ques_action)
# print('大模型输出------------',out_put)
# sql = extract_sql(out_put)
# print('最终sql',sql)
# sql_result = db.run_no_str(sql)
# print("数据库查询结果",sql_result)
# dic_sql_res = result_record(sql_result)
# print(result_record(sql_result))
# print('======================',out_result(dic_sql_res))