#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from autoagents.roles import Role
from autoagents.system.logs import logger
from autoagents.system.schema import Message
from autoagents.actions import NextAction

CONTENT_TEMPLATE ="""
## Previous Steps and Responses
{previous}

## Current Step
{step}
"""

class ActionObserver(Role):
    def __init__(self, steps, init_actions, watch_actions, name="Alex", profile="ActionObserver", goal="Effectively delivering information according to plan.",
                 constraints="", **kwargs):
        self.steps = steps
        self.next_step = ''
        self.next_role = ''
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions(init_actions)
        self._watch(watch_actions)
        self.next_action = NextAction()
        self.necessary_information = ''

    async def _think(self) -> None:
        self.steps.pop(0)        
        if len(self.steps) > 0:
            states_prompt = ''
            for i, step in enumerate(self.steps):
                states_prompt += str(i+1) + ':' + step + '\n'

            self.next_action.set_prefix(self._get_prefix(), self.profile, self._proxy, self._llm_api_key, self._serpapi_api_key)
            task = self._rc.important_memory[0]
            content = [task, str(self._rc.env.new_roles_args), str(self._rc.important_memory), states_prompt]
            rsp = await self.next_action.run(content)

            self.next_step = self.steps[0] # rsp.instruct_content.NextStep
            next_state = 0

            self.necessary_information = rsp.instruct_content.NecessaryInformation 
            print('*******Next Steps********')
            print(states_prompt)
            print('************************')

            next_state, min_idx = 0, 100
            for i, state in enumerate(self._actions):
                class_name = re.findall('(.*?)_Requirement', str(state))[0].replace('_', ' ')
                next_state = i
                self.next_role = class_name
                if class_name == self.next_step.split(':')[0]:
                    break

            self._set_state(next_state)
        else:
            self.next_step = ''
            self.next_role = ''


    async def _act(self) -> Message:

        if self.next_step == '':
            return Message(content='', role='')

        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        content = CONTENT_TEMPLATE.format(previous=self.necessary_information, step=self.next_step)
        msg = Message(content=content, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        return msg