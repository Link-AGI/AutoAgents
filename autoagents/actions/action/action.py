#!/usr/bin/env python
# coding: utf-8
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/actions/action.py
"""
from abc import ABC
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_fixed

from .action_output import ActionOutput
from autoagents.system.llm import LLM
from autoagents.system.utils.common import OutputParser
from autoagents.system.logs import logger

class Action(ABC):
    def __init__(self, name: str = '', context=None, llm: LLM = None, serpapi_api_key=None):
        self.name: str = name
        # if llm is None:
        #     llm = LLM(proxy, api_key)
        self.llm = llm
        self.context = context
        self.prefix = ""
        self.profile = ""
        self.desc = ""
        self.content = ""
        self.serpapi_api_key = serpapi_api_key
        self.instruct_content = None

    def set_prefix(self, prefix, profile, proxy, api_key, serpapi_api_key):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile
        self.llm = LLM(proxy, api_key)
        self.serpapi_api_key = serpapi_api_key

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        return await self.llm.aask(prompt, system_msgs)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def _aask_v1(self, prompt: str, output_class_name: str,
                       output_data_mapping: dict,
                       system_msgs: Optional[list[str]] = None) -> ActionOutput:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        content = await self.llm.aask(prompt, system_msgs)
        logger.debug(content)
        output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)
        parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)
        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(content, instruct_content)

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
