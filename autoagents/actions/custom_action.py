#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import json
from typing import List, Tuple

from autoagents.actions.action import Action
from .action.action_output import ActionOutput
from .action_bank.search_and_summarize import SearchAndSummarize, SEARCH_AND_SUMMARIZE_SYSTEM_EN_US

from autoagents.system.logs import logger
from autoagents.system.utils.common import OutputParser
from autoagents.system.schema import Message
from autoagents.system.const import WORKSPACE_ROOT
from autoagents.system.utils.common import CodeParser

PROMPT_TEMPLATE = '''
-----
{role} Base on the following execution result of the previous agents and completed steps and their responses, complete the following tasks as best you can. 

# Task {context}

# Suggestions
{suggestions}

# Execution Result of Previous Agents {previous}

# Completed Steps and Responses {completed_steps} 

You have access to the following tools:
# Tools {tool}

# Steps
1. You should understand and analyze the execution result of the previous agents.
2. You should understand, analyze, and break down the task and use tools to assist you in completing it.
3. You should analyze the completed steps and their outputs and identify the current step to be completed, then output the current step in the section 'CurrentStep'.
3.1 If there are no completed steps, you need to analyze, examine, and decompose this task. Then, you should solve the above tasks step by step and design a plan for the necessary steps, and accomplish the first one.
3.2 If there are completed steps, you should grasp the completed steps and determine the current step to be completed. 
4. You need to choose which Action (one of the [{tool}]) to complete the current step. 
4.1 If you need use the tool 'Write File', the 'ActionInput' MUST ALWAYS in the following format:
```
>>>file name
file content
>>>END
```
4.2 If you have completed all the steps required to finish the task, use the action 'Final Output' and summarize the outputs of each step in the section 'ActionInput'. Provide a detailed and comprehensive final output that solves the task in this section. Please try to retain the information from each step in the section 'ActionInput'. The final output in this section should be helpful, relevant, accurate, and detailed.


# Format example
Your final output should ALWAYS in the following format:
{format_example}

# Attention
1. The input task you must finish is {context}
2. DO NOT ask any questions to the user or human.
3. The final output MUST be helpful, relevant, accurate, and detailed.
-----
'''

FORMAT_EXAMPLE = '''
---
## Thought 
you should always think about what step you need to complete now and how to complet this step.

## Task
the input task you must finish

## CurrentStep
the current step to be completed

## Action
the action to take, must be one of [{tool}]

## ActionInput
the input to the action
---
'''

OUTPUT_MAPPING = {
    "CurrentStep": (str, ...),
    "Action": (str, ...),
    "ActionInput": (str, ...),
}

INTERMEDIATE_OUTPUT_MAPPING = {
    "Step": (str, ...),
    "Response": (str, ...),
    "Action": (str, ...),
}

FINAL_OUTPUT_MAPPING = {
    "Step": (str, ...),
    "Response": (str, ...),
}

class CustomAction(Action):

    def __init__(self, name="CustomAction", context=None, llm=None, **kwargs):
        super().__init__(name, context, llm, **kwargs)

    def _save(self, filename, content):        
        file_path = os.path.join(WORKSPACE_ROOT, filename)

        if not os.path.exists(WORKSPACE_ROOT):
            os.mkdir(WORKSPACE_ROOT)

        with open(file_path, mode='w+', encoding='utf-8') as f:
            f.write(content)
        
    async def run(self, context):
        # steps = ''
        # for i, step in enumerate(list(self.steps)):
        #     steps += str(i+1) + '. ' + step + '\n'

        previous_context = re.findall(f'## Previous Steps and Responses([\s\S]*?)## Current Step', str(context))[0]
        task_context = re.findall('## Current Step([\s\S]*?)### Completed Steps and Responses', str(context))[0]
        completed_steps = re.findall(f'### Completed Steps and Responses([\s\S]*?)###', str(context))[0]
        # print('-------------Previous--------------')
        # print(previous_context)
        # print('--------------Task-----------------')
        # print(task_context)
        # print('--------------completed_steps-----------------')
        # print(completed_steps)
        # print('-----------------------------------')
        # exit()
        
        tools = list(self.tool) + ['Print', 'Write File', 'Final Output']
        prompt = PROMPT_TEMPLATE.format(
            context=task_context,
            previous=previous_context,
            role=self.role_prompt,
            tool=str(tools),
            suggestions=self.suggestions,
            completed_steps=completed_steps,
            format_example=FORMAT_EXAMPLE
        )

        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)

        if 'Write File' in rsp.instruct_content.Action:
            filename = re.findall('>>>(.*?)\n', str(rsp.instruct_content.ActionInput))[0]
            content = re.findall(f'>>>{filename}([\s\S]*?)>>>END', str(rsp.instruct_content.ActionInput))[0]
            self._save(filename, content)
            response = f"\n{rsp.instruct_content.ActionInput}\n"
        elif rsp.instruct_content.Action in self.tool:
            sas = SearchAndSummarize(serpapi_api_key=self.serpapi_api_key, llm=self.llm)
            sas_rsp = await sas.run(context=[Message(rsp.instruct_content.ActionInput)], system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
            # response = f"\n{sas_rsp}\n"
            response = f">>> Search Results\n{sas.result}\n\n>>> Search Summary\n{sas_rsp}"
        else:
            response = f"\n{rsp.instruct_content.ActionInput}\n"

        if 'Final Output' in rsp.instruct_content.Action:
            info = f"\n## Step\n{task_context}\n## Response\n{completed_steps}>>>> Final Output\n{response}\n>>>>"
            output_class = ActionOutput.create_model_class("task", FINAL_OUTPUT_MAPPING)
            parsed_data = OutputParser.parse_data_with_mapping(info, FINAL_OUTPUT_MAPPING)
        else:
            info = f"\n## Step\n{task_context}\n## Response\n{response}\n## Action\n{rsp.instruct_content.CurrentStep}\n"
            output_class = ActionOutput.create_model_class("task", INTERMEDIATE_OUTPUT_MAPPING)
            parsed_data = OutputParser.parse_data_with_mapping(info, INTERMEDIATE_OUTPUT_MAPPING)
        
        instruct_content = output_class(**parsed_data)

        return ActionOutput(info, instruct_content)

