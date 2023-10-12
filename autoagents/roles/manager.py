#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Iterable, Type

from pydantic import BaseModel, Field

from autoagents.actions import Requirement, CreateRoles, CheckRoles, CheckPlans
from autoagents.roles import Role

from autoagents.actions import Action, ActionOutput
from autoagents.system.config import CONFIG
from autoagents.system.llm import LLM
from autoagents.system.logs import logger
from autoagents.system.memory import Memory, LongTermMemory
from autoagents.system.schema import Message

class Manager(Role):
    def __init__(self, name="Ethan", profile="Manager", goal="Efficiently to finish the tasks or solve the problem",
                 constraints="", serpapi_key=None, **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([CreateRoles, CheckRoles, CheckPlans])
        self._watch([Requirement])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        roles_plan, suggestions_roles, suggestions_plan = '', '', ''
        suggestions, num_steps = '', 3

        steps, consensus = 0, False
        while not consensus and steps < num_steps:
            self._set_state(0)
            response = await self._rc.todo.run(self._rc.important_memory, history=roles_plan, suggestions=suggestions)
            roles_plan = str(response.instruct_content)
            if 'No Suggestions' not in suggestions_roles or 'No Suggestions' not in suggestions_plan:
                self._set_state(1)
                history_roles = f"## Role Suggestions\n{suggestions_roles}\n\n## Feedback\n{response.instruct_content.RoleFeedback}"
                _suggestions_roles = await self._rc.todo.run(response.content, history=history_roles)
                suggestions_roles += _suggestions_roles.instruct_content.Suggestions

                self._set_state(2)
                history_plan = f"## Plan Suggestions\n{suggestions_roles}\n\n## Feedback\n{response.instruct_content.PlanFeedback}"
                _suggestions_plan = await self._rc.todo.run(response.content, history=history_plan)
                suggestions_plan += _suggestions_plan.instruct_content.Suggestions

            suggestions = f"## Role Suggestions\n{_suggestions_roles.instruct_content.Suggestions}\n\n## Plan Suggestions\n{_suggestions_plan.instruct_content.Suggestions}"
                
            if 'No Suggestions' in suggestions_roles and 'No Suggestions' in suggestions_plan:
                consensus = True

            steps += 1

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        return msg