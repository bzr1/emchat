# -*- coding: utf-8 -*-
from langchain.utilities.sql_database import SQLDatabase
import copy
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from paramslist import OPENAI_API_KEY_X2,OPENAI_API_KEY_X3,DATABASE_URL_X,OPENAI_KEY2,OPENAI_API_BASE_X,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME


class Embed_chrom_solutionChain:
    def __init__(self):
        # self.openai_key = OPENAI_API_KEY_X3
        # self.openai_base = OPENAI_API_BASE_X
        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
                              openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        # self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_X3, openai_api_base=OPENAI_API_BASE_X, temperature=0)
        # self.llm = ChatOpenAI(openai_api_key=OPENAI_KEY2,temperature=0)
        # self.memory = ConversationBufferMemory(return_messages=True)

        template = """
        你是一个专业信息提取助手,不需要回答key中的问题。不要输出与问题无关的内容.更不要私自添加任何信息。
        
        用户的{input}中包含了key,和action两部分，key里面含有关键信息的值,action是输出模板,请从key中提取关键信息填入action中,输出修改后的action

        请根据input中的key,提取到对应action中需要的目标信息,并替换其中的信息后直接返回给用户action. 

        示例1：
        用户输入：key:隐患基站阜新阜新县十家子镇7381903-H5H相关的告警有什么？action:查询re_result表，字段NAME = 'CCC';
        助手输出：action:查询re_result表，字段NAME = '阜新阜新县十家子镇7381903-H5H';

        示例2:
        用户输入:key:请查询小区A-JZ-WLMQWSGAJDL-HLW-1在2022年4月22日10点的流量情况。action:查询traffic_predict表，字段cell_name = 'XXX',字段time = '2022-04-22 10:00:00';
        助手输出:action:查询traffic_predict表，字段cell_name = 'A-JZ-WLMQWSGAJDL-HLW-1',字段time = '2022-04-22 10:00:00';
        
        示例3：
        用户输入:key:基站[辽阳灯塔市政达沥青拌合站215467TDD-HLP]在2023年3月23日是否派发故障工单？action:查询result_solution_order表，字段NAME='[XXX]'， 字段FAULTOCCURCALENDAR::date = '2023-04-03' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';
        助手输出:action:查询result_solution_order表，字段NAME='[辽阳灯塔市政达沥青拌合站215467TDD-HLP]'， 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';

        请严格按照例子中的格式返回action给用户.返回的action中字段名不包含中括号。如果action中有字段NAME='XXX',请注意该部分填充时不要有‘基站’两字，如果所提取的含有‘基站’，请务必去掉这两个字。
       

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
        output1 = self.chain.invoke({"input":input})
        print('第一个embed:',output1.content)
        output = output1
        # sta = int(input.split('key')[0])
        # if sta == 3:
        #     chain_emd = Embed_se()
        #     output = chain_emd.predict(output1.content)
        # else:
        #     output = output1
        return output


class Embed_se:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME,
                              openai_api_base=OPENAI_API_BASE_QW, temperature=0)


        template = """
        你是一个检查信息是否正确的助手，只需执行下面的流程，无需添加任何信息。
        
        用户输入的{input}格式为action:查询XX表……
        
        首先：请检查输入的信息中是否包含 字段NAME='XXX' 。
        如果含有字段NAME='XXX' 请检查XXX中前两个字是否是‘基站’二字，如果检查到则去掉这两个字后返回，如果未检查到则直接把{input}原封返回。
        
        如果检查输入的信息{input}中不含有  字段NAME='XXX'这样的信息 则直接把{input}原封返回。
        
        示例1：
        用户输入：action:查询result_solution_order表，字段NAME='基站大连高新园区吉粮大厦948726TDD-ZLP'， 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';
        助手输出：action:查询result_solution_order表，字段NAME='大连高新园区吉粮大厦948726TDD-ZLP'， 字段FAULTOCCURCALENDAR::date = '2023-03-23' AND FAULTOCCURCALENDAR::time >= '00:00:00' AND FAULTOCCURCALENDAR::time <= '23:59:59';
        
        示例2：
        用户输入：action:查询re_result表，字段NAME = '阜新阜新县十家子镇7381903-H5H';
        助手输出：action:查询re_result表，字段NAME = '阜新阜新县十家子镇7381903-H5H';

        
        请严格按照示例输出，要么去掉基站二字，要么返回原始输入的内容给用户。
        
    
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
        output = self.chain.invoke({"input": input})
        return output



# if __name__ == '__main__':
#     conver = Embed_chrom_solutionChain()
#     while True:
#         q = input('请输入问题:')
#         output = conver.predict(q)
#         print(output.content)