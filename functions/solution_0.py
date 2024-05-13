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
from paramslist import DATABASE_URL, OPENAI_API_KEY_X3, DATABASE_URL_X, OPENAI_KEY2, OPENAI_API_BASE_X,OPENAI_API_BASE_QW,OPENAI_API_KEY_QW,MODEL_NAME
# import openai
# openai.api_base = "http://localhost:8000/v1"
# openai.api_key = "none"
pg_uri = DATABASE_URL_X
db = SQLDatabase.from_uri(pg_uri)


class Status_0_solutionChain:
    def __init__(self):

        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME, openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        self.memory = ConversationBufferMemory(return_messages=True)

        template = """
        你是一个专业postgres SQL生成助手,不需要回答question的问题.

        用户的{input}中包含了question和action两部分,你无需在意question的内容,只需要根据action的内容生成准确的sql语句返回给用户.


        示例：
        用户输入：question:请分析丹东所有华为基站的top10高隐患基站情况 action: 查询re_result表，字段manufacturer = '华为' ，字段 prefecture = '丹东' 字段，bshealthdegree DESC LIMIT 10;
        助手输出:SELECT * FROM re_result WHERE manufacturer = '华为' AND prefecture = '丹东' ORDER BY bshealthdegree DESC LIMIT 10;
        
        请严格按照例子中的格式返回sql语句给用户,不要带有其他文字.
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self, input: str):
        output = self.conversation.predict(input=input)
        return output


class Status_chatChain():
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY_QW, model_name=MODEL_NAME, openai_api_base=OPENAI_API_BASE_QW, temperature=0)

        self.memory = ConversationBufferMemory(return_messages=True)

        template = "You are a nice chatbot having a conversation with a human."
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.conversation = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def predict(self, input: str):
        output = self.conversation.predict(input=input)
        return output


def out_result2_1(data):
    # data = [dict(zip(columns, row)) for row in rows]
    column_names = {
        "bshealthdegree": "基站健康度异常程度",
        "keyalarmitem": "整治重点告警项目",
        "faultcause": "故障原因类别",
        "predictprobability": "预测未来退服概率",
        "name": "所属基站",
        "manufacturer": "厂家",
        "prefecture": "所属地市",
    }
    transformed_data = []
    for item in data:
        transformed_item = {}
        for key, value in item.items():
            if key in column_names:
                transformed_item[column_names[key]] = value
        transformed_data.append(transformed_item)
    if not transformed_data:
        return '未查询到信息'
    else:
        result = "查询得到该区域隐患基站清单如下：<br>"
        i = 0
        for item in transformed_data:
            print(item)
            if i < 11:
                i += 1
                res = f"{i}、基站{item['所属基站']}\t {item['基站健康度异常程度']} \t {item['整治重点告警项目']} \t {item['故障原因类别']} \t {item['预测未来退服概率']} \n"
                result += res
        result = result.replace('\t', '&nbsp;' * 4)
        result = result.replace('\n', '<br>')

        return result


def result2_1_record(reords):
    print(len(reords), type(reords))
    new_records = []
    for rec in reords:
        print("*****************************************")
        print(rec, len(rec), type(rec))
        dict_rec = {}
        dict_rec['bshealthdegree'] = rec[3]
        dict_rec['keyalarmitem'] = rec[4]
        dict_rec['faultcause'] = rec[6]
        dict_rec['predictprobability'] = rec[7]
        dict_rec['name'] = rec[8]
        dict_rec['manufacturer'] = rec[24]
        dict_rec['prefecture'] = rec[25]
        new_records.append(copy.deepcopy(dict_rec))
    return new_records


def get_0_result(sql):
    query_result = db.run_no_str(sql)
    print('0---数据库查询信息', query_result)
    record = result2_1_record(query_result)
    print(record)
    result = out_result2_1(record)
    return result

# aaa =  [(datetime.date(2023, 4, 2), datetime.date(2023, 4, 8), 1, Decimal('2.00000000000000000000'), "'(69)射频单元CPRI接口异常告警(90.72%)', '(64)射频单元时钟异常告警(6.21%)', '(121)用户面故障告警(1.09%)', '(53)BBU CPRI接口异常告警(0.88%)', '(16)小区不可用告警(0.72%)'", '射频单元CPRI接口异常告警：254次, 射频单元时钟异常告警：9次, 用户面故障告警：1次, BBU CPRI接口异常告警：5次, 小区不可用告警：15次', 'IR接口,时钟,传输,退服', Decimal('0.65958445703693360000'), '丹东凤城市青城子林家矿业145354FDD-HLH', '连续多天异常(7);', Decimal('3.00000000000000000000'), '1.0', '2.0', None, '0,1,2,3,4,5,6', None, None, None, '空', 145354, 145354, '丹东桃源无线机房', '非VIP', '入网在用', '华为', '丹东', '凤城市', '丹东', '室外', '4G', '检查前传光缆； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复： 1、检查本端和对端的配置是否正确； 2、检查是否存在单板硬件故障； 3、检查是否存在底层链路故障； 4、检查证书是否失效； 检查前传光缆是否正常；'), (datetime.date(2023, 4, 3), datetime.date(2023, 4, 9), 1, Decimal('2.00000000000000000000'), "'(69)射频单元CPRI接口异常告警(75.49%)', '(64)射频单元时钟异常告警(17.08%)', '(53)BBU CPRI接口异常告警(4.96%)', '(16)小区不可用告警(1.58%)'", '射频单元CPRI接口异常告警：281次, 射频单元时钟异常告警：22次, BBU CPRI接口异常告警：16次, 小区不可用告警：33次', 'IR接口,时钟,退服', Decimal('0.61391032698341240000'), '丹东凤城市青城子林家矿业145354FDD-HLH', '连续多天异常(7);', Decimal('4.00000000000000000000'), '1.0', '1.0', '2.0', '0,1,2,3,4,5,6', None, None, None, None, 145354, 145354, '丹东桃源无线机房', '非VIP', '入网在用', '华为', '丹东', '凤城市', '丹东', '室外', '4G', '检查前传光缆； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复： 检查前传光缆是否正常；'), (datetime.date(2023, 3, 30), datetime.date(2023, 4, 5), 1, Decimal('2.00000000000000000000'), "'(19)小区接收通道干扰噪声功率不平衡告警(97.71%)', '(121)用户面故障告警(2.12%)'", '小区接收通道干扰噪声功率不平衡告警：105次, 用户面故障告警：2次', '天馈和驻波,传输', Decimal('0.40745358091468400000'), '丹东凤城市林家台村八组隧道048768TFD-HLR', '连续多天异常(7);', Decimal('1.00000000000000000000'), None, None, None, '0,1,2,3,4,5,6', None, None, None, '空', 48768, 48768, '丹东高铁林家台村八组无线机房', '未查询到', '入网在用', '华为', '丹东', '凤城市', '丹东', '室外', '4G', '1、检查本端和对端的配置是否正确； 2、检查是否存在单板硬件故障； 3、检查是否存在底层链路故障； 4、检查证书是否失效；'), (datetime.date(2023, 3, 31), datetime.date(2023, 4, 6), 1, Decimal('2.00000000000000000000'), "'(69)射频单元CPRI接口异常告警(90.69%)', '(64)射频单元时钟异常告警(5.02%)', '(121)用户面故障告警(1.81%)', '(53)BBU CPRI接口异常告警(1.13%)', '(123)X2接口故障告警(0.57%)'", '射频单元CPRI接口异常告警：178次, 射频单元时钟异常告警：6次, 用户面故障告警：2次, BBU CPRI接口异常告警：4次, X2接口故障告警：4次', 'IR接口,时钟,传输', Decimal('0.56435346764452770000'), '丹东凤城市青城子林家矿业145354FDD-HLH', '连续多天异常(6);', Decimal('2.00000000000000000000'), None, None, '21.0', '0,1,2,3,4,5', None, None, None, '空', 145354, 145354, '丹东桃源无线机房', '非VIP', '入网在用', '华为', '丹东', '凤城市', '丹东', '室外', '4G', '检查前传光缆； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复： 1、检查本端和对端的配置是否正确； 2、检查是否存在单板硬件故障； 3、检查是否存在底层链路故障； 4、检查证书是否失效； 检查前传光缆是否正常；'), (datetime.date(2023, 3, 30), datetime.date(2023, 4, 5), 1, Decimal('2.00000000000000000000'), "'(55)射频单元CPRI接口异常告警(88.35%)', '(43)BBU CPRI接口异常告警(9.08%)', '(70)射频单元维护链路异常告警(1.40%)', '(51)射频单元时钟异常告警(1.17%)'", '射频单元CPRI接口异常告警：264次, BBU CPRI接口异常告警：27次, 射频单元维护链路异常告警：2次, 射频单元时钟异常告警：1次', 'IR接口,传输,时钟', Decimal('0.70415153775281800000'), '丹东凤城市通远堡高铁站5G7373749-H5W', '连续多天异常(7);', Decimal('4.00000000000000000000'), '2.0', '2.0', '3.0', '0,1,2,3,4,5,6', None, None, None, None, 7373749, 7373749, '丹东凤城通远堡高铁站资源点', '未查询到', '预开通', '华为', '丹东', '凤城市', '丹东', '室内', '5G', '检查前传光缆； 检查前传光缆是否正常； 1、检查RRU射频单元是否掉电、未上电； 2、检查BBU到RRU的收发光； 3、检查BBU与RRU之间的光纤、光模块，光模块要求两端厂家、型号、速率一样； 4、使用倒换或者更换逐个排除BBU单板、RRU射频模块、光纤、光模块； 5、更换坏件； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复：'), (datetime.date(2023, 3, 31), datetime.date(2023, 4, 6), 1, Decimal('2.00000000000000000000'), "'(55)射频单元CPRI接口异常告警(90.01%)', '(43)BBU CPRI接口异常告警(7.77%)', '(70)射频单元维护链路异常告警(1.21%)', '(51)射频单元时钟异常告警(1.01%)'", '射频单元CPRI接口异常告警：269次, BBU CPRI接口异常告警：27次, 射频单元维护链路异常告警：2次, 射频单元时钟异常告警：1次', 'IR接口,传输,时钟', Decimal('0.56937468945096670000'), '丹东凤城市通远堡高铁站5G7373749-H5W', '连续多天异常(7);', Decimal('4.00000000000000000000'), '2.0', '2.0', '2.0', '0,1,2,3,4,5,6', None, None, None, None, 7373749, 7373749, '丹东凤城通远堡高铁站资源点', '未查询到', '预开通', '华为', '丹东', '凤城市', '丹东', '室内', '5G', '检查前传光缆； 检查前传光缆是否正常； 1、检查RRU射频单元是否掉电、未上电； 2、检查BBU到RRU的收发光； 3、检查BBU与RRU之间的光纤、光模块，光模块要求两端厂家、型号、速率一样； 4、使用倒换或者更换逐个排除BBU单板、RRU射频模块、光纤、光模块； 5、更换坏件； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复：'), (datetime.date(2023, 4, 1), datetime.date(2023, 4, 7), 1, Decimal('2.00000000000000000000'), "'(55)射频单元CPRI接口异常告警(91.23%)', '(43)BBU CPRI接口异常告警(6.71%)', '(70)射频单元维护链路异常告警(1.13%)'", '射频单元CPRI接口异常告警：281次, BBU CPRI接口异常告警：27次, 射频单元维护链路异常告警：2次', 'IR接口,传输', Decimal('0.54777791305433910000'), '丹东凤城市通远堡高铁站5G7373749-H5W', '连续多天异常(7);', Decimal('4.00000000000000000000'), '1.0', '2.0', '2.0', '0,1,2,3,4,5,6', None, None, None, None, 7373749, 7373749, '丹东凤城通远堡高铁站资源点', '未查询到', '预开通', '华为', '丹东', '凤城市', '丹东', '室内', '5G', '检查前传光缆； 检查前传光缆是否正常； 1、检查RRU射频单元是否掉电、未上电； 2、检查BBU到RRU的收发光； 3、检查BBU与RRU之间的光纤、光模块，光模块要求两端厂家、型号、速率一样； 4、使用倒换或者更换逐个排除BBU单板、RRU射频模块、光纤、光模块； 5、更换坏件；'), (datetime.date(2023, 3, 27), datetime.date(2023, 4, 2), 1, Decimal('2.00000000000000000000'), "'(31)MME衍生小区退服(46.35%)', '(3)MME衍生基站退服(43.82%)', '(108)网元连接中断(7.99%)', '(59)S1接口故障告警(1.83%)'", 'MME衍生小区退服：110次, MME衍生基站退服：151次, 网元连接中断：22次, S1接口故障告警：3次', '其他,脱管和退服,传输', Decimal('0.73795034130030410000'), '丹东凤城市凤城北庙村13组007546FDD-HLH', '连续多天异常(7);', Decimal('4.00000000000000000000'), '9.0', '1.0', '1.0', '0,1,2,3,4,5,6', None, None, None, None, 7546, 7546, '丹东北庙无线机房', '未查询到', '工程状态', '华为', '丹东', '凤城市', '丹东', '室外', '4G', None), (datetime.date(2023, 4, 1), datetime.date(2023, 4, 7), 1, Decimal('2.00000000000000000000'), "'(69)射频单元CPRI接口异常告警(93.15%)', '(64)射频单元时钟异常告警(3.46%)', '(121)用户面故障告警(1.52%)', '(53)BBU CPRI接口异常告警(0.68%)', '(16)小区不可用告警(0.56%)'", '射频单元CPRI接口异常告警：210次, 射频单元时钟异常告警：6次, 用户面故障告警：2次, BBU CPRI接口异常告警：4次, 小区不可用告警：12次', 'IR接口,时钟,传输,退服', Decimal('0.57843967559234690000'), '丹东凤城市青城子林家矿业145354FDD-HLH', '连续多天异常(7);', Decimal('2.00000000000000000000'), '2.0', None, None, '0,1,2,3,4,5,6', None, None, None, '空', 145354, 145354, '丹东桃源无线机房', '非VIP', '入网在用', '华为', '丹东', '凤城市', '丹东', '室外', '4G', '检查前传光缆； 远端修复：远程复位射频单元，判断告警是否恢复： 近端修复：更换射频单元，判断告警是否恢复： 1、检查本端和对端的配置是否正确； 2、检查是否存在单板硬件故障； 3、检查是否存在底层链路故障； 4、检查证书是否失效； 检查前传光缆是否正常；'), (datetime.date(2023, 3, 17), datetime.date(2023, 3, 23), 9, Decimal('1.00000000000000000000'), "'(58)制式间通信异常告警(99.56%)'", '制式间通信异常告警：1次', '硬件板卡', Decimal('0.34244936720414240000'), '丹东振安区临江街电业局145125FDD-HLH', '连续多天异常(2);', Decimal('1.00000000000000000000'), None, None, None, '0,2', None, None, None, None, 145125, 145125, '丹东振安区临江街电业局资源点', '非VIP', '入网在用', '华为', '丹东', '振安区', '丹东', '室外', '4G', '1、检查BBU内单板是否存在硬件故障告警或其它软件运行异常告警； 2、通知厂家人员检查数据配置是否存在问题')]
