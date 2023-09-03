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

        completed_steps, responses, todo = '', '', ''

        addition = f"\n### Completed Steps\n{completed_steps} \n\n### Responses of Previous Steps\n{responses}\n ### TODO Steps\n{todo}\n ###"

        context = str(self._rc.important_memory) + addition

        response = await self._rc.todo.run(context)

        completed_steps += response.instruct_content.CurrentStep
        responses += response.instruct_content.Response
        todo = response.instruct_content.TODO

        count_steps = 0
        while 'None' not in response.instruct_content.TODO:
            if count_steps > 5:
                todo = 'You should synthesize the responses of previous steps and provide the final feedback.'
            
            addition = f"\n### Completed Steps\n{completed_steps} \n\n### Responses of Previous Steps\n{responses}\n ### TODO Steps\n{todo}\n ###"

            context = str(self._rc.important_memory) + addition

            response = await self._rc.todo.run(context)

            responses += f"\n\n{response.instruct_content.Response}\n" 

            # print(response.instruct_content)

            # if hasattr(response.instruct_content, 'TODO'):
            #     completed_steps += f"\n\n{response.instruct_content.CurrentStep}\n"
            #     todo = f"\n\n{response.instruct_content.TODO}\n"
            # else:
            #     todo = 'None'

            completed_steps += f"\n\n{response.instruct_content.CurrentStep}\n"
            todo = f"\n\n{response.instruct_content.TODO}\n"

            count_steps += 1

        # response.instruct_content.Response = responses
        response.instruct_content.CurrentStep = ''
        response.instruct_content.TODO = ''

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        return msg