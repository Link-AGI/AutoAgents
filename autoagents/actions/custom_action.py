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
# Previous
Here is the execution result of the previous agents:
{previous}

# Task
Here is the task you need to complete. You should understand, analyze, and break down this task and use tools to assist you in completing it.
You can solve the above tasks step by step, ensuring that you need to output as much detailed content as possible to solve the problem
{context}

# Role
{role} 

# Tools
{tool}

# Steps
{steps} 

# Completed Steps
{completed_steps} 

# TODO Steps
{todo}

# Responses of Previous Steps
{responses} 

# Attention
The task that you need to complete is "{context}".

# Format example
Your final output should ALWAYS in the following format:
{format_example}
-----
'''

FORMAT_EXAMPLE = '''
---
# Task
The task you need to complete.

# Thought 
1. To complete the current step, you should make full use of the execution results of previous agents.
2. When there are no completed or TODO steps, you need to analyze, examine, and decompose this task. Next, you should design a plan for the necessary steps, and accomplish the first one.
3. If there are completed steps, you should grasp the completed steps and think about how to complete the todo steps and what additional steps might be required to improve the results. 
4. If there are no additional steps to add, you need to synthesize the responses of previous steps and the current step, and provide the final feedback. 

# Output:
Following is the output of your standardized feedback or conclusion

## Type
There are three types of output [ACTION/PRINT/FILE]:
1. ACTION: Call the tool in the Section Tools to get more information
2. PRINT: Directly output the final result
3. FILE: Save the output as a file

## Key
This indicates the necessary information for different types of output:
1. ACTION needs to specify the name of the tool of the Section Tools.
2. PRINT needs to declare Final Answer in the Section 'Key'
3. FILE needs to declare multiple filename in the Section 'Key'

## Content
This is the specific content of the different types of output
1. The input of the TOOLS.
2. The output of the PRINT
3. ```
The detail content of the FILE (Note that only one file can be written at a time)
```
File Summary: the summary of the FILE

## CurrentStep
Output the content that needs to be completed in this step

## TODO
1. Here is a list of steps that you still need to work on for solving the original task. 
2. You should examine the input ## TODO and see if there are any steps that are not finished. If yes, please list them here.
3. If there is nothing to do, only output 'None'. Do not output 'None' when there are todo steps.
'''

# 3. The purpose of the steps in TODO is to solve the original task “{context}”.
# You should also think about how to enhance the quality of your results with these extra steps.

OUTPUT_MAPPING = {
    "CurrentStep": (str, ...),
    "Type": (str, ...),
    "Key": (str, ...),
    "Content": (str, ...),
    "TODO": (str, ...),
}

FINAL_OUTPUT_MAPPING = {
    "Step": (str, ...),
    "Response": (str, ...),
    "CurrentStep": (str, ...),
    "TODO": (str, ...),
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
        steps = ''
        for i, step in enumerate(list(self.steps)):
            steps += str(i+1) + '. ' + step + '\n'

        # print(context)
        previous_context = re.findall(f'## Previous Steps and Responses([\s\S]*?)## Current Step', str(context))[0]
        task_context = re.findall('## Current Step([\s\S]*?)### Completed Steps', str(context))[0]
        completed_steps = re.findall(f'### Completed Steps([\s\S]*?)### Responses of Previous Steps', str(context))[0]
        responses = re.findall(f'### Responses of Previous Steps([\s\S]*?)### TODO Steps', str(context))[0]
        todo = re.findall(f'### TODO Steps([\s\S]*?)###', str(context))[0]
        # print('--------------Task-----------------')
        # print(task_context)
        # print('-------------Previous--------------')
        # print(previous_context)
        # print('--------------completed_steps-----------------')
        # print(completed_steps)
        # print('-------------responses--------------')
        # print(responses)
        # print('--------------todo-----------------')
        # print(todo)
        # print('-----------------------------------')
        
        prompt = PROMPT_TEMPLATE.format(
            context=task_context,
            previous=previous_context,
            role=self.role_prompt,
            tool=str(self.tool),
            steps=steps,
            completed_steps=completed_steps,
            todo=todo,
            responses=responses,
            format_example=FORMAT_EXAMPLE
        )

        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)

        if 'ACTION' in rsp.instruct_content.Type:
            sas = SearchAndSummarize(serpapi_api_key=self.serpapi_api_key, llm=self.llm)
            sas_rsp = await sas.run(context=[Message(rsp.instruct_content.Content)], system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
            response = f"\n{sas_rsp}\n"
        elif 'PRINT' in rsp.instruct_content.Type:
            response = f"\n{rsp.instruct_content.Content}\n"
        elif 'FILE' in rsp.instruct_content.Type:
            filename = rsp.instruct_content.Key
            file_type = re.findall('```(.*?)\n', str(rsp.content))[0]
            # summary = re.findall('File Summary:(.*?)', str(rsp.content))[0]
            content = re.findall(f'```{file_type}([\s\S]*?)```', str(rsp.content))[0]
            # info = f"\n## Step\n{context} \n\n ## Response\n{summary}\n"
            
            self._save(filename, content)
            response = f"### FILE: {filename}\n{content}\n"

        # if 'None' not in rsp.instruct_content.TODO:
        #     info = f"\n## Step\n{task_context} \n\n ## Response\n{response}\n ## CurrentStep\n{rsp.instruct_content.CurrentStep}\n ## TODO\n{rsp.instruct_content.TODO}\n"
        # else:
        #     info = f"\n## Step\n{task_context} \n\n ## Response\n{response}\n"
        info = f"\n## Step\n{task_context} \n\n ## Response\n{response}\n ## CurrentStep\n{rsp.instruct_content.CurrentStep}\n ## TODO\n{rsp.instruct_content.TODO}\n"

        output_class = ActionOutput.create_model_class("task", FINAL_OUTPUT_MAPPING)
        parsed_data = OutputParser.parse_data_with_mapping(info, FINAL_OUTPUT_MAPPING)
        instruct_content = output_class(**parsed_data)

        return ActionOutput(info, instruct_content)

