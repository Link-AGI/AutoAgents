#!/usr/bin/env python
# -*- coding: utf-8 -*-

from autoagents.actions import CheckRoles, CheckPlans, CreateRoles
from autoagents.roles import Role
from autoagents.system.logs import logger


class ObserverAgents(Role):
    def __init__(self, name="Eric", profile="Agents Observer", goal="Check if the created Expert Roles following the requirements",
                 constraints="", **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([CheckRoles])
        self._watch([CreateRoles])


class ObserverPlans(Role):
    def __init__(self, name="Gary", profile="Plan Observer", goal="Check if the created Execution Plan following the requirements",
                 constraints="", **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([CheckPlans])
        self._watch([CreateRoles,CheckRoles])

    async def _observe(self) -> int:
        """从环境中观察，获得全部重要信息，并加入记忆"""
        if not self._rc.env:
            return 0
        env_msgs = self._rc.env.memory.get()
        
        observed = self._rc.env.memory.get_by_and_actions(self._rc.watch)
        
        news = self._rc.memory.remember(observed)  # remember recent exact or similar memories

        for i in env_msgs:
            self.recv(i)

        news_text = [f"{i.role}: {i.content[:20]}..." for i in news]
        if news_text:
            logger.debug(f'{self._setting} observed: {news_text}')
        return len(news)