#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Iterable, Type

from pydantic import BaseModel, Field

from autoagents.roles import Role
from autoagents.actions import CustomAction, Action, ActionOutput

# from autoagents.environment import Environment
from autoagents.system.config import CONFIG
from autoagents.system.llm import LLM
from autoagents.system.logs import logger
from autoagents.system.memory import Memory, LongTermMemory
from autoagents.system.schema import Message

class CustomRole(Role):
    def __init__(self, role_prompt, steps, tool, watch_actions,
                name="CustomRole", 
                profile="CustomeRole", 
                goal="Efficiently to finish the tasks",
                constraints="",
                **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        class_name = name.replace(' ', '_')+'_Action'
        action_object = type(class_name, (CustomAction,), {"role_prompt":role_prompt, "steps":steps, "tool":tool})
        self._init_actions([action_object])
        self._watch(watch_actions)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        completed_steps = ''
        addition = f"\n### Completed Steps and Responses\n{completed_steps}\n###"
        context = str(self._rc.important_memory) + addition
        response = await self._rc.todo.run(context)

        if hasattr(response.instruct_content, 'Action'):
            completed_steps += '>Substep:\n' + response.instruct_content.Action + '\n>Subresponse:\n' + response.instruct_content.Response + '\n'

        count_steps = 0
        while hasattr(response.instruct_content, 'Action'):
            if count_steps > 20:
                completed_steps += '\n You should synthesize the responses of previous steps and provide the final feedback.'
            
            addition = f"\n### Completed Steps and Responses\n{completed_steps}\n###"
            context = str(self._rc.important_memory) + addition
            response = await self._rc.todo.run(context)

            if hasattr(response.instruct_content, 'Action'):
                completed_steps += '>Substep:\n' + response.instruct_content.Action + '\n>Subresponse:\n' + response.instruct_content.Response + '\n'

            count_steps += 1

            if count_steps > 20: break

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        return msg