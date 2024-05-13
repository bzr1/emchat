# -*- coding: utf-8 -*-
import textwrap
import time

# -*- coding: utf-8 -*-
import textwrap
import time
from typing import List

from langchain.chat_models import ChatOpenAI

from langchain.agents import initialize_agent, AgentType, ConversationalAgent, ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import StringPromptTemplate
from langchain.tools import Tool, BaseTool

from paramslist import OPENAI_API_KEY, OPENAI_API_BASE, PREDICT_ALARM_FILE_FOLDER
from paramslist import OPENAI_API_KEY_QW, OPENAI_API_BASE_QW, MODEL_NAME
from agents.tools.ops_predict_tool_class import OpsPredictTool
from agents.tools.ops_optim_tool_class import OpsOptimTool
from agents.tools.ops_rca_tool_class import OpsRcaTool
from agents.tools.traffic_predict_tool_class import TrafficPredictTool

from agents.custom_output_parser import CustomOutputParser


def output_response(response: str) -> None:
    if not response:
        exit(0)
    for line in textwrap.wrap(response, width=60):
        for word in line.split():
            for char in word:
                print(char, end="", flush=True)
                time.sleep(0.1)  # Add a delay of 0.1 seconds between each character
            print(" ", end="", flush=True)  # Add a space between each word
        print()  # Move to the next line after each line is printed
    print("----------------------------------------------------------------")



AGENT_TMPL = """
按照给定的格式回答以下通信专业问题,用中文完成对话。你可以自行回答给出针对性建议,或使用下面这些工具：

{tools}

回答时需要遵循以下用---括起来的格式：

---

Question: 我需要回答的问题
Thought: 回答这个上述我需要做些什么
Action: ”{tool_names}“ 中的其中一个工具名
Action Input: 选择工具所需要的输入
Observation: 选择工具返回的结果
...（这个思考/行动/行动输入/观察可以重复N次）
Thought: 我现在知道最终答案
Final Answer: 原始输入问题的最终答案
---

现在开始回答，记得在给出最终答案前多按照指定格式进行一步一步的推理。
若用户提到[给出建议]、[优化方案]或[提出解决方案]，请不要使用工具，自行给出建议或优化方案。

Question: {input}
{agent_scratchpad}

以下用***括起来的是示例：
***
示例1：
chat_history:HumanMessage(content='请实时对ID-151-20210801-00010工单进行根因分析'), AIMessage(content='根因分析结果如下:名为 ID-151-20210801-00010 的故障工单，告警原因为无线及设备原因-GPS。')
question: 针对ID-151-20210801-00010工单有什么解决方案？
Thought: Do I need to use a tool? No
AI: ID-151-20210801-00010工单的告警原因是无线及设备原因-GPS，建议检查无线设备、GPS设备。

示例2：
chat_history:HumanMessage(content='请分析沈阳大东区上园路7号-上园路13-1号051178TDD-HLY基站未来的退服概率'), AIMessage(content="\\n        分析预测结果如下:名为 沈阳大东区上园路7号-上园路13-1号051178TDD-HLY 的 51178 号基站 未来一周的退服概率为0.0754。            \\n        名为 沈阳大东区上园路7号-上园路13-1号051178TDD-HLY 的 51178 号基站，位于辽宁省沈阳市，由华为提供的4G网络。\\n            读取预处理该基站 2022-11-06 至 2022-11-12 告警数据，启动基站退服预测能力调用。\\n        该基站在 2022-11-06 至 2022-11-12 期间的告警记录为：\\n            [[\'2022-11-07 13:38:05\', \'用户面承载链路故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-07 13:38:05\', \'2022-11-07\', \'2022-11-07\', \'2022-11-07 13:00:00\'], [\'2022-11-09 00:29:55\', \'X2接口故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-09 00:29:55\', \'2022-11-09\', \'2022-11-09\', \'2022-11-09 00:00:00\'], [\'2022-11-09 00:38:03\', \'X2接口故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-09 00:38:03\', \'2022-11-09\', \'2022-11-09\', \'2022-11-09 00:00:00\'], [\'2022-11-09 01:04:21\', \'X2接口故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-09 01:04:21\', \'2022-11-09\', \'2022-11-09\', \'2022-11-09 01:00:00\'], [\'2022-11-09 08:59:05\', \'X2接口故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-09 08:59:05\', \'2022-11-09\', \'2022-11-09\', \'2022-11-09 08:00:00\'], [\'2022-11-09 12:08:31\', \'X2接口故障告警\', 51178, \'沈阳大东区上园路7号-上园路13-1号051178TDD-HLY\', \'2022-11-09 12:08:31\', \'2022-11-09\', \'2022-11-09\', \'2022-11-09 12:00:00\']]\\n        ")
question: 针对该基站的退服概率，请给出合理的处理建议
Thought: Do I need to use a tool? No
AI: 沈阳大东区上园路7号-上园路13-1号051178TDD-HLY基站未来一周的退服概率为0.0754。针对用户面承载链路故障告警，检查并修复链路故障；针对X2故障告警，检查X2接口的状态和配置；密切关注基站性能指标和运行状态，定期检查电源、传输设备、天线等关键部件的工作情况。请根据实际情况进行相应处理和维护工作
***
"""
# chat_history: {chat_history}

class CustomPromptTemplate(StringPromptTemplate):
    template: str  # 标准模板
    tools: List[BaseTool]  # 可使用工具集合

    def format(self, **kwargs) -> str:
        """
        按照定义的 template，将需要的值都填写进去。

        Returns:
            str: 填充好后的 template。
        """
        intermediate_steps = kwargs.pop("intermediate_steps")  # 取出中间步骤并进行执行
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts  # 记录下当前想法
        kwargs["tools"] = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools]
        )  # 枚举所有可使用的工具名+工具描述
        kwargs["tool_names"] = ", ".join(
            [tool.name for tool in self.tools]
        )  # 枚举所有的工具名称
        cur_prompt = self.template.format(**kwargs)
        print(cur_prompt)
        return cur_prompt



def init_agent():
    llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)

    tools = [
        OpsPredictTool(),
        OpsOptimTool(),
        OpsRcaTool(),
        TrafficPredictTool()
    ]

    prompt = CustomPromptTemplate(
        template=AGENT_TMPL,
        tools=tools,
        input_variables=["input", "intermediate_steps"],
        # input_variables=["chat_history", "input", "intermediate_steps"],
        tool_names=[tool.name for tool in tools]
    )
    output_parser = CustomOutputParser()
    # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = ConversationalAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True, handle_parsing_errors=True,
                                                   output_parser=output_parser, stop=["\nObservation:"])
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True,memory=None,
                                                        handle_parsing_errors=True)
    # agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory,
    #                                                     handle_parsing_errors=True)
    return agent_executor


def use_memory_agent(human_input: str):
    # llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
    # llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)
    llm = ChatOpenAI(model_name=MODEL_NAME, openai_api_key=OPENAI_API_KEY_QW, openai_api_base=OPENAI_API_BASE_QW)

    tools = [
        OpsPredictTool(),
        OpsOptimTool(),
        OpsRcaTool()
    ]

    prompt = CustomPromptTemplate(
        template=AGENT_TMPL,
        tools=tools,
        input_variables=["chat_history", "input", "intermediate_steps"],
        tool_names = [tool.name for tool in tools]
    )
    output_parser = CustomOutputParser()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = ConversationalAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True, handle_parsing_errors=True,
                                                   output_parser=output_parser, stop=["\nObservation:"])
    # agent = ZeroShotAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True, handle_parsing_errors=True)
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    # agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors=True)
    epoch = 0
    while True:
        try:
            user_input = human_input if epoch == 0 else input("请输入您的问题：")
            epoch += 1
            response = agent_executor.run(user_input)
            # agent_executor.memory.save_context({"input": user_input}, {"output": str(response)})
            output_response(response)
        except KeyboardInterrupt:
            break


def output_response(response: str) -> None:
    if not response:
        exit(0)
    for line in textwrap.wrap(response, width=60):
        for word in line.split():
            for char in word:
                print(char, end="", flush=True)
                time.sleep(0.1)  # Add a delay of 0.1 seconds between each character
            print(" ", end="", flush=True)  # Add a space between each word
        print()  # Move to the next line after each line is printed
    print("----------------------------------------------------------------")




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # input_text = "请实时对ID-151-20210801-00010工单进行根因分析"
    # input_text = "hello"
    # input_text = "请分析长沙中南工大升华大楼-H5H-D59002490534PT-2612在2023年11月10日的网络状态"
    input_text = input("请输入您的问题：")
    # use_memory_agent(input_text)