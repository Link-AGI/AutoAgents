#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autoagents.actions import ActionOutput, SearchAndSummarize
from autoagents.logs import logger
from autoagents.roles import Role
from autoagents.schema import Message
from autoagents.tools import SearchEngineType


class Searcher(Role):
    def __init__(self, name='Alice', profile='Smart Assistant', goal='Provide search services for users',
                 constraints='Answer is rich and complete', engine=SearchEngineType.SERPAPI_GOOGLE, **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([SearchAndSummarize(engine=engine)])

    def set_search_func(self, search_func):
        action = SearchAndSummarize("", engine=SearchEngineType.CUSTOM_ENGINE, search_func=search_func)
        self._init_actions([action])

    async def _act_sp(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        response = await self._rc.todo.run(self._rc.memory.get(k=0))
        # logger.info(response)
        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                            role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

    async def _act(self) -> Message:
        return await self._act_sp()
