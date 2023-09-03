"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""
from autoagents.provider.anthropic_api import Claude2 as Claude
from autoagents.provider.openai_api import OpenAIGPTAPI as LLM

DEFAULT_LLM = LLM()
CLAUDE_LLM = Claude()


async def ai_func(prompt):
    return await DEFAULT_LLM.aask(prompt)
