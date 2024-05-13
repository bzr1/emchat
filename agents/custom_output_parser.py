import re
from typing import Union
from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish


class CustomOutputParser(AgentOutputParser):
    ai_prefix: str = "AI"
    """Prefix to use before AI output."""

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # print(type(text))
        print(text)
        # if "retirement rate" in text:
        #     return AgentFinish(
        #         return_values={"output": text.split("Observation:")[-1].strip()},
        #         log=text,
        #     )
        if "Final Answer:" in text:  # 如果句子中包含 Final Answer 则代表已经完成
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text,
            )
        if f"{self.ai_prefix}:" in text:
            return AgentFinish(
                {"output": text.split(f"{self.ai_prefix}:")[-1].strip()}, text
            )
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, text)
        if not match:
            return AgentFinish(
                {"output": text.split(f"{self.ai_prefix}:")[-1].strip()}, text
            )
            # raise OutputParserException(f"Could not parse LLM output: `{text}`")
        action = match.group(1)
        action_input = match.group(2)
        return AgentAction(action.strip(), action_input.strip(" ").strip('"'), text)
