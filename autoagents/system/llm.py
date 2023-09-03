"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
@From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/llm.py
"""
from .provider.anthropic_api import Claude2 as Claude
from .provider.openai_api import OpenAIGPTAPI as LLM

DEFAULT_LLM = LLM()
CLAUDE_LLM = Claude()


async def ai_func(prompt):
    return await DEFAULT_LLM.aask(prompt)
