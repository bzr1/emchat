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
from paramslist import DATABASE_URL,DATABASE_URL_X,OPENAI_API_KEY_X3,OPENAI_API_BASE_X,OPENAI_API_KEY_QW,OPENAI_API_BASE_QW,MODEL_NAME

pg_uri = DATABASE_URL_X
db = SQLDatabase.from_uri(pg_uri)




class Status_8_solutionChain:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
                              openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        self.memory = ConversationBufferMemory(return_messages=True)

        # template ="""
        #    You are a helpful assistant to return results based on user input.
        # 1.This type of problem generates postgres SQL query statements for users,don't with any other word.
        # If the question in user's input like that:请查询小区XXX在2022年4月22日10点的流量情况。
        # then you need to generate postgresql queries based on the action entered by the user.Please only returned postgresSQL query statements are returned because I need to query directly to the database.
        #
        # """
        template ="""
         你是一个根据用户输入不同返回针对性信息的助手。
        假如用户输入中的question是如下示例：请查询小区XXX在2022年4月22日10点的流量情况。
        那么根据用户输入中的action对应的表名，字段信息，生成postgresql，只返回postgresql，用于直接去数据库进行查询，不要带有文字。
        示例：
        input:
            question:请查询小区A-JZ-WLMQWSGAJDL-HLW-1在2022年4月22日10点的流量情况。action:查询traffic_predict表，字段cell_name = 'A-JZ-WLMQWSGAJDL-HLW-1',字段time = '2022-04-22 10:00:00';
        output：
            SELECT * FROM traffic_predict WHERE cell_name = 'A-JZ-WLMQWSGAJDL-HLW-1' AND time = '2022-04-22 10:00:00'; 
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self,input:str):
        output = self.conversation.predict(input=input)
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
        dict_rec['cell_name'] = rec[0]
        # dict_rec['time'] = rec[1]
        dict_rec['wire_con_rate'] = rec[2]
        dict_rec['wire_util_rate'] = rec[3]
        dict_rec['handle_suc_rate'] = rec[4]
        dict_rec['wire_drop_rate'] = rec[5]
        dict_rec['up_prb'] = rec[6]
        dict_rec['down_prb'] = rec[7]
        dict_rec['up_kb'] = rec[8]
        dict_rec['down_kb'] = rec[9]
        # dict_rec['weekday'] = rec[10]
        # dict_rec['hour'] = rec[11]
        new_records.append(copy.deepcopy(dict_rec))
    return new_records



def out_result(data):
    # data = [dict(zip(columns, row)) for row in rows]
    column_names = {
        # 'cell_name': '小区',
        'wire_con_rate': '无线接通率',
        'wire_util_rate': '无线利用率',
        'handle_suc_rate': '切换成功率',
        'wire_drop_rate': '无线掉线率',
        'up_prb': '上行PRB平均利用率',
        'down_prb': '下行PRB平均利用率',
        'up_kb': '上行流量 (Kbyte)',
        'down_kb': '下行流量 (Kbyte)',
        # 'his032': 'gNB间Xn切换成功率(SA)',
        # 'his033': 'gNB间NG切换成功率(SA)'
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
        result = "该小区流量数据标查询结果如下：<br>"
        for item in transformed_data:
            print(item)
            for key,value in item.items():
                if value:
                    result += key + ':' + value + '; <br>'
    else:
        result = '未查询到相关信息'
    return result



def get_8_result(sql,conversation):
    query_result = db.run_no_str(sql)
    if (isinstance(query_result, list) and len(query_result) > 0):
        resu_sql = result_record(query_result)
        conversation.memory.save_context({"input": sql}, {"output": str(resu_sql)})
    else:
        resu_sql = []
    resu_sql = out_result(resu_sql)
    return resu_sql



# conversation = Status_8_solutionChain()
# ques_action = "question:请查询小区A-JZ-WLMQWSGAJDL-HLW-1在2022年4月22日18点的流量情况。action:查询traffic_predict表，字段cell_name = 'A-JZ-WLMQWSGAJDL-HLW-1',字段time = '2022-04-22 18:00:00';"
# res = conversation.predict(input=ques_action)
# print(res)
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