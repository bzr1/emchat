# -*- coding: utf-8 -*-
from langchain.utilities.sql_database import SQLDatabase
import copy
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from paramslist import DATABASE_URL, DATABASE_URL_X, OPENAI_API_KEY_X3, OPENAI_API_BASE_X,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME,ID_DOC_LIST

pg_uri = DATABASE_URL_X
db = SQLDatabase.from_uri(pg_uri)


class Status_3_solutionChain:
    def __init__(self):

        self.llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW, temperature=0)
        self.memory = ConversationBufferMemory(return_messages=True)
        self.history_list = []


        # template = """
        # You are a helpful assistant to return results based on user's input.
        # 1.This type of problem generates postgres SQL query statements for users.
        # if human input like that: 基站XXX近期是否派发故障工单？or XXX基站在2023年4月3日是否派发故障工单？or 基站XXX在2023年4月3日是否派发故障工单？
        # then you need to generate postgresql queries based on the action entered by the user's input.Only returned postgresSQL query statements are returned because I need to query directly to the database.
        #
        # 2.The following question queries the data stored in memory and returns the corresponding result directly to the user, not sql.
        # If the question in the user's input  like that: 该工单派发前发生过哪些告警？or 该故障发生前出现过哪些告警？or 请帮我查询该工单相关的告警？
        # then will output information corresponding to the field 'wirealarm' and 'subcategory' and output format example:"无线告警: XXXX \n 专题大类: XXXX"
        # else if the question in the user's input  like that: 这些告警故障原因解释是什么？or 请为我解释一下这些告警的故障原因? or 这些告警由什么原因引起的？
        # then will output information corresponding to the field 'faultexplanation' and output format example:"故障原因解释: XXXX"
        # else if the question in the user's input  like that: 如何对该基站的故障进行处理? or 请告诉我如何处理该故障?
        # then will output information corresponding to the field 'proposalterat' and output format example:"处理方案建议: XXXX"
        # """


        template = """
        
      
        你是一个根据用户输入不同返回针对性信息的助手。不要输出与问题无关的内容.更不要私自添加任何信息。
        用户的{input}中包含了question和action两部分。
        1. This type of problem generates postgres SQL query statements for users.
        假如用户输入中的question是如下示例：基站XXX近期是否派发故障工单？or XXX基站在2023年4月3日是否派发故障工单？or 基站XXX在2023年4月3日是否派发故障工单？
        那么根据用户{input}中的action对应的表名，以及字段信息，要严格按照sql的格式生成postgresql，不可随意增加无用字符，只返回postgresql，用于直接去数据库进行查询，不要带有文字。
        
        示例：
        input:question:基站辽阳灯塔市政达沥青拌合站215467TDD-HLP在2023年3月23日是否派发故障工单？action:查询result_solution_order表，字段NAME='辽阳灯塔市政达沥青拌合站215467TDD-HLP', 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';
        output: SELECT * FROM result_solution_order WHERE NAME='辽阳灯塔市政达沥青拌合站215467TDD-HLP' AND FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';


        2.The following question queries the data stored in memory and returns the corresponding result directly to the user, not sql.
         If the question in the user's input  like that: 该工单派发前发生过哪些告警？or 该故障发生前出现过哪些告警？or 请帮我查询该工单相关的告警？
         那么按照这个思路解决：首先，请忽视掉用户输入中的action中的所有内容。然后请根据本对话保存的历史信息中，找到字典中key为'wirealarm'的键值对，以及key为subcategory的键值对， 如果未找到请重新检查自己的历史对话，里面HumanMessage存的content是SQL语句，AIMessage存入的content就包含这个参数。如果找到多条信息，则合并返回，'wirealarm'表示无线告警.'subcategory'表示专题大类。
        返回的示例如下：key = 'wirealarm'对应的value替换AAA，key = 'subcategory'的value替换BBB:
        无线告警: AAA \n 
        专题大类: BBB
        
         else if the question in the user's input  like that: 这些告警故障原因解释是什么？or 请为我解释一下这些告警的故障原因? or 这些告警由什么原因引起的？
         按照这个思路解决：首先，请忽视掉用户输入中的action中的所有内容。然后请根据本对话保存的历史信息中，找到'faultexplanation'的键值对，'faultexplanation'表示故障原因解释。
        返回的示例如下,'faultexplanation'的值替换XXXX:
        故障原因解释: XXXX
       
       else if the question in the user's input  like that: 如何对该基站的故障进行处理? or 请告诉我如何处理该故障?
            如何对该基站的故障进行处理? or 请告诉我如何处理该故障?
        按照这个解决思路：首先，请忽视掉用户输入中的action中的所有内容。然后请根据本对话保存的历史信息中，找到'proposalterat'对应的键值对，'proposalterat'表示处理方案建议。
        返回的示例如下，'proposalterat'的值替换XXXX：
        处理方案建议: XXXX
        
        
        按照以上各情况的解决思路进行处理用户的input，请勿把历史保存的整个列表信息返回给用户。
        
        示例： 
        用户输入:question:请为我解释一下这些告警的故障原因？action:触发查询历史信息回答对应问题。
        助手输出:
            故障原因解释: XXXX
        
        用户输入：question: 请告诉我如何处理该故障？action: 触发查询历史信息回答对应问题。
        助手输出：
            处理方案建议: XXXX
            
        用户输入：question:请帮我查询该工单相关的告警？action:触发查询历史信息回答对应问题。
        助手输出：
            无线告警: XXXX \n 专题大类: XXXX
        
        请以示例的格式输出最终结果，无需添加其他文字。
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self, input,id_doc):
        output = self.conversation.predict(input=input)
        print("STEP3=====converstation output:\n", output)
        history3 = self.conversation.memory.load_memory_variables({})
        print(history3)
        print('\n保存到的列表\n',self.history_list)
        if id_doc in ID_DOC_LIST and self.history_list:
            solution_history = SolutionHistory()
            quest = input.split('action')[0]
            quest = quest.split('question')[-1]
            data = self.history_list
            input_q_d={'question':quest,'data':data}

            output = solution_history.predict(input=str(input_q_d),data=data)

        return output


class SolutionHistory:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
                              openai_api_base=OPENAI_API_BASE_QW, temperature=0)




        template = """
        你是一个帮助用户提取数据信息并按模板整合返回的助手。
        用户输入的{input}格式为字典格式，question对应的值表示问题，data对应的值表示数据。根据一下思路解决各类问题。
        1.如果用户{input}的问题是下面这几个：
            这些告警故障原因解释是什么？ or 请为我解释一下这些告警的故障原因? or 这些告警由什么原因引起的？
            那么按照这个思路解决：根据data中的信息中， 找到key为'faultexplanation'的键值对，'faultexplanation'表示故障原因解释。
        返回的示例如下,'faultexplanation'的值替换XXXX:
            故障原因解释: XXXX
       
        2.如果用户{input}的问题是下面这几个：
            如何对该基站的故障进行处理? or 请告诉我如何处理该故障?
            那么按照这个思路解决：根据data中的信息中， 找到key为'proposalterat'对应的键值对，'proposalterat'表示处理方案建议。
        返回的示例如下，'proposalterat'的值替换XXXX：
            处理方案建议: XXXX
        
        3.如果用户{input}的问题是下面这几个： 
            该工单派发前发生过哪些告警？or 该故障发生前出现过哪些告警？or 请帮我查询该工单相关的告警？
            那么按照这个思路解决：根据data中的信息中， 找到key为'wirealarm'的键值对，以及key为subcategory的键值对，'wirealarm'表示无线告警.'subcategory'表示专题大类。
        返回的示例如下：key = 'wirealarm'对应的value替换AAA，key = 'subcategory'的value替换BBB:
            无线告警: AAA 
            专题大类: BBB
        
        请严格按照各类问题的示例格式回答问题，不要添加任何别的文字。

        """
        template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=template),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        self.chain = template | ChatOpenAI(
            model_name=MODEL_NAME,
            openai_api_key=OPENAI_API_KEY_QW,
            openai_api_base=OPENAI_API_BASE_QW, temperature=0,
            streaming=True)

    def predict(self, input,data):
        # print(input)
        output = self.chain.invoke({"input":input}).content.strip()
        output = output.replace('\t', '&nbsp;' * 4)
        output = output.replace('\n', '<br>')

        return output


def parse_record(reords):
    new_records = []
    for rec in reords:
        dict_rec = {}
        dict_rec['manufacturer'] = rec[11]
        dict_rec['nettype'] = rec[9]
        dict_rec['occurarea'] = rec[4]
        dict_rec['faultoccurcalendar'] = rec[5]
        dict_rec['title'] = rec[8]
        # dict_rec['wirealarm'] = rec[23] + '\n专题大类：'+rec[24]
        dict_rec['wirealarm'] = rec[23]
        dict_rec['subcategory'] = rec[24]
        dict_rec['proposalterat'] = rec[29]
        dict_rec['faultexplanation'] = rec[30]
        new_records.append(copy.deepcopy(dict_rec))
    return new_records


def out_put_data(data):
    # data = [dict(zip(columns, row)) for row in rows]
    column_names = {
        "manufacturer": "厂家",
        "nettype": "网络分类",
        "occurarea": "发生地区",
        "faultoccurcalendar": "故障发生时间",
        "title": "工单标题",
    }

    transformed_data = []
    for item in data:
        transformed_item = {}
        for key, value in item.items():
            if key in column_names:
                transformed_item[column_names[key]] = value
        transformed_data.append(transformed_item)

    print(data)
    if not transformed_data:
        return '未查询到信息'
    else:
        output = ""
        for item in transformed_data:
            output += f"发生地区：{item['发生地区']} <br>厂家:{item['厂家']} <br>故障发生时间:{item['故障发生时间'].strftime('%Y.%m.%d %H:%M:%S')} <br>工单标题:{item['工单标题']} <br>网络分类:{item['网络分类']} <br> ------------------------------------------------------------------------------------------------------------ <br>"

        print("******************************", output)
        return output


def get_3_result(sql, conversation):
    query_result = db.run_no_str(sql)
    print(query_result)
    if (isinstance(query_result, list) and len(query_result) > 0):
        resu_sql = parse_record(query_result)
        conversation.memory.save_context({"input": sql}, {"output": str(resu_sql)})
        conversation.history_list = resu_sql
    else:
        resu_sql = []

    if len(resu_sql[0]) > 2:
        resu_sql = out_put_data(resu_sql)

    return resu_sql


import re
def extract_sql_3(text):
    '''
    :param text:大模型返回的内容
    :return: 如果是SQL查询，则返回SQL，否则返回原内容
    '''
    sql_query_match1 = re.search(r'(?<=SELECT).*?(?=;)', text, re.DOTALL)
    sql_query_match2 = re.search(r'(?<=SELECT).*?(?=；)', text, re.DOTALL)
    sql_query_match3 = None
    pattern = r"SELECT .*'23:59:59'"
    match = re.findall(pattern, text)
    for sql in match:
        sql_query_match3 = sql + ';'
        print(3,sql_query_match3)
    # print(sql_query_match1,sql_query_match2)FAULTOCCURCALENDAR::time <= '23:59:59';
    if sql_query_match1:
        sql_query = "SELECT " + sql_query_match1.group().strip() + ";"
        print('1',sql_query)
        return sql_query
    elif sql_query_match2:
        sql_query = "SELECT " + sql_query_match2.group().strip() + ";"
        print('2', sql_query)
        return sql_query
    else:
        return sql_query_match3
# from functions.solution_5 import extract_sql
# text = "question:基站辽阳灯塔市政达沥青拌合站215467TDD-HLP在2023年3月23日是否派发故障工单？action:查询result_solution_order表，字段NAME='辽阳灯塔市政达沥青拌合站215467TDD-HLP'， 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';"
# question:请为我解释一下这些告警的故障原因？action:触发查询历史信息回答对应问题。 1
# question:这些告警故障原因解释是什么？action:触发查询历史信息回答对应问题。 1
# question:请告诉我如何处理该故障？action:触发查询历史信息回答对应问题。3
# question:如何对该基站的故障进行处理？action:触发查询历史信息回答对应问题。3
# q2 = "question:请帮我查询该工单相关的告警？action:触发查询历史信息回答对应问题。"  回答有误2
# q2 = "question:该工单派发前发生过哪些告警？action:触发查询历史信息回答对应问题。"
# q2 = "question:该故障发生前出现过哪些告警？action:触发查询历史信息回答对应问题。"
# conversation = Status_3_solutionChain()
# while True:
#     input_data = input('请输入问题：')
#     res = conversation.predict(input = input_data)
#     print(res)
#     sql = extract_sql(res)
#     print(sql)
    # status_list.append(status)
    # if sql.startswith("SELECT"):
    #     result_return = get_3_result(sql, conversation)
    # else:
    #     result_return = sql
    # print(result_return)
#

# question:基站大连高新园区吉粮大厦948726TDD-ZLP在2023年3月23日是否派发故障工单？action:查询result_solution_order表，字段NAME='大连高新园区吉粮大厦948726TDD-ZLP'， 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';
#
# import datetime
# data_list =  [{'manufacturer': '华为', 'nettype': '无线/LTE无线网/eNodeB', 'occurarea': '辽阳', 'faultoccurcalendar': datetime.datetime(2023, 3, 23, 9, 31, 52), 'title': '[移动][无线]辽阳市：辽阳灯塔市政达沥青拌合站215467TDD-HLP 上报 基站退服', 'wirealarm': "['RHUB交流掉电告警', '基站退服']", 'subcategory': "['动力', '其他']", 'proposalterat': "['联系维护人员检测电源是否正常', '']", 'faultexplanation': "['当AC-DC模块的RHUB的外部交流电源输入中断时，产生此告警。', '']"}]
# conversation = SolutionHistory()
# while True:
#     input_data = input('请输入问题：')
#     input_data = 'question:'+input_data
#     input_q_d = {'question': input_data, 'data': data_list}
#     res = conversation.predict(input = str(input_q_d),data=data_list).content.strip()
#     print(res)
