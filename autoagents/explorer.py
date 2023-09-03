#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@Modified From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/software_company.py
"""
from pydantic import BaseModel, Field

from .roles import Role
from .actions import Requirement
from .environment import Environment

from .system.config import CONFIG
from .system.logs import logger
from .system.schema import Message
from .system.utils.common import NoMoneyException


class Explorer(BaseModel):
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    
    class Config:
        arbitrary_types_allowed = True

    def hire(self, roles: list[Role]):
        self.environment.add_roles(roles)

    def invest(self, investment: float):
        self.investment = investment
        CONFIG.max_budget = investment
        logger.info(f'Investment: ${investment}.')

    def _check_balance(self):
        if CONFIG.total_cost > CONFIG.max_budget:
            raise NoMoneyException(CONFIG.total_cost, f'Insufficient funds: {CONFIG.max_budget}')

    async def start_project(self, idea=None, llm_api_key=None, proxy=None, serpapi_key=None, task_id=None, alg_msg_queue=None):
        self.environment.llm_api_key = llm_api_key
        self.environment.proxy = proxy
        self.environment.task_id = task_id
        self.environment.alg_msg_queue = alg_msg_queue
        self.environment.serpapi_key = serpapi_key
        
        await self.environment.publish_message(Message(role="Question/Task", content=idea, cause_by=Requirement))

    def _save(self):
        logger.info(self.json())

    async def run(self, n_round=3):
        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.environment.run()
        return self.environment.history
