#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
from autoagents.actions import Action, ActionOutput
from autoagents.roles import Role
from autoagents.system.logs import logger
from autoagents.system.schema import Message
from autoagents.actions import NextAction, CustomAction, Requirement

SLEEP_RATE = 30 # sleep between calls

CONTENT_TEMPLATE ="""
## Previous Steps and Responses
{previous}

## Current Step
{step}
"""

class Group(Role):
    def __init__(self, roles, steps, watch_actions, name="Alex", profile="Group", goal="Effectively delivering information according to plan.", constraints="", **kwargs):
        self.steps = steps
        self.roles = roles
        self.next_state = []
        self._watch_action = watch_actions[-1]
        super().__init__(name, profile, goal, constraints, **kwargs)
        init_actions = []
        for role in self.roles:
            print('Add a new role:', role['name'])
            class_name = role['name'].replace(' ', '_')+'_Action'
            action_object = type(class_name, (CustomAction,), {"role_prompt":role['prompt'], "suggestions":role['suggestions'], "tool":role['tools']})
            init_actions.append(action_object)
        self._init_actions(init_actions)
        self._watch(watch_actions)
        self.next_action = NextAction()
        self.necessary_information = ''
        self.next_action.set_prefix(self._get_prefix(), self.profile, self._proxy, self._llm_api_key, self._serpapi_api_key)

    async def _think(self) -> None:        
        if len(self.steps) > 1:
            self.steps.pop(0)
            states_prompt = ''
            for i, step in enumerate(self.steps):
                states_prompt += str(i+1) + ':' + step + '\n'
            
            # logger.info(f"{self._setting}: ready to {self.next_action}")
            # task = self._rc.important_memory[0]
            # content = [task, str(self._rc.env.new_roles_args), str(self._rc.important_memory), states_prompt]
            # rsp = await self.next_action.run(content)

            self.next_step = self.steps[0]
            next_state = 0

            # self.necessary_information = rsp.instruct_content.NecessaryInformation 
            print('*******Next Steps********')
            print(states_prompt)
            print('************************')
            self.next_state = []                
            for i, state in enumerate(self._actions):
                name = str(state).replace('_Action', '').replace('_', ' ')
                if name in self.next_step.split(':')[0]:
                    self.next_state.append(i)
        else:
            if len(self.steps) > 0:
                self.steps.pop(0)
            self.next_step = ''
            self.next_role = ''

    async def _act(self) -> Message:
        if self.next_step == '':
            return Message(content='', role='')
        
        completed_steps, num_steps = '', 5
        message = CONTENT_TEMPLATE.format(previous=str(self._rc.important_memory), step=self.next_step)
        # context = str(self._rc.important_memory) + addition

        steps, consensus = 0, [0 for i in self.next_state]
        while len(self.next_state) > sum(consensus) and steps < num_steps:

            if steps > num_steps - 2:
                completed_steps += '\n You should synthesize the responses of previous steps and provide the final feedback.'
                
            for i, state in enumerate(self.next_state):
                self._set_state(state)
                logger.info(f"{self._setting}: ready to {self._rc.todo}")

                addition = f"\n### Completed Steps and Responses\n{completed_steps}\n###"
                context = message + addition
                response = await self._rc.todo.run(context)

                if hasattr(response.instruct_content, 'Action'):
                    completed_steps += f'>{self._rc.todo} Substep:\n' + response.instruct_content.Action + '\n>Subresponse:\n' + response.instruct_content.Response + '\n'
                else:
                    consensus[i] = 1
                time.sleep(SLEEP_RATE)

            steps += 1

        # response.content = completed_steps
        requirement_type = type('Requirement_Group', (Requirement,), {})
        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content, cause_by=self._watch_action)
        else:
            msg = Message(content=response, cause_by=self._watch_action)
        # self._rc.memory.add(msg)

        return msg

    async def _observe(self) -> int:
        """从环境中观察，获得全部重要信息，并加入记忆"""
        if not self._rc.env:
            return 0
        env_msgs = self._rc.env.memory.get()
        
        observed = self._rc.env.memory.get_by_actions(self._rc.watch)
        
        news = self._rc.memory.remember(observed)  # remember recent exact or similar memories

        for i in env_msgs:
            self.recv(i)

        news_text = [f"{i.role}: {i.content[:20]}..." for i in news]
        if news_text:
            logger.debug(f'{self._setting} observed: {news_text}')
        return len(news)