#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
from typing import List, Tuple

from autoagents.logs import logger
from autoagents.actions.action import Action
from autoagents.actions.action_output import ActionOutput
from autoagents.utils.common import OutputParser
from autoagents.schema import Message
from autoagents.const import WORKSPACE_ROOT
from autoagents.actions.search_and_summarize import SearchAndSummarize, SEARCH_AND_SUMMARIZE_SYSTEM_EN_US
from autoagents.utils.common import CodeParser

PROMPT_TEMPLATE = '''
-----
# Previous
Here is the execution result of the previous steps
{previous}

# Task
Here is the task you must to complete. You must understand, analyze, and disassemble this task.
{context}

# Role
{role} 

# Tools
{tool}

# Steps
{steps} 

# Format example
Your final output should ALWAYS in the following format:
{format_example}
-----
'''

FORMAT_EXAMPLE = '''
---
# Task
the task of the current step

# Thought 
you should always think about how to complete the current task

# Output:
Following is the output of your standardized feedback or conclusion

## Type
There are three types of output [ACTION/PRINT/FILE]:
1. ACTION: Call the tool in the Section Tools to get more information
2. PRINT: Directly output the final result
3. FILE: Save the output as a file, for writing code or document tasks

## Key
This indicates the necessary information for different types of output:
1. ACTION needs to specify the name of the tool of the Section Tools in the Section 'Key'
2. PRINT needs to declare Final Answer in the Section 'Key'
3. FILE needs to declare multiple filename in the Section 'Key'

## Content
This is the specific content of the different types of output
1. The input of the ACTION
2. The output of the PRINT
3. ```
The detail content of the FILE
```
File Summary: the summary of the FILE
'''

OUTPUT_MAPPING = {
    "Type": (str, ...),
    "Key": (str, ...),
    "Content": (str, ...),
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
        steps = ''
        for i, step in enumerate(list(self.steps)):
            steps += str(i+1) + '. ' + step + '\n'

        task_context = re.findall('## Current Step([\s\S]*?)]', str(context))[-1]
        previous_context = re.findall(f'## Previous Steps and Responses([\s\S]*?)## Current Step', str(context))[0]
        # print('-------------Context--------------')
        # print(context)
        # print('--------------Task-----------------')
        # print(task_context)
        # print('-------------Previous--------------')
        # print(previous_context)
        # print('-----------------------------------')

        prompt = PROMPT_TEMPLATE.format(
            context=task_context,
            previous=previous_context,
            role=self.role_prompt,
            tool=self.tool,
            steps=steps,
            format_example=FORMAT_EXAMPLE
            )
                
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)

        if 'ACTION' in rsp.instruct_content.Type:
            sas = SearchAndSummarize(serpapi_api_key=self.serpapi_key, llm=self.llm)
            rsp = await sas.run(context=[Message(rsp.instruct_content.Content)], system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
            info = f"\n## Step\n{task_context} \n\n ## Response\n{rsp}\n"    
        elif 'PRINT' in rsp.instruct_content.Type:
            info = f"\n## Step\n{task_context} \n\n ## Response\n{rsp.instruct_content.Content}\n"
        elif 'FILE' in rsp.instruct_content.Type:
            filename = rsp.instruct_content.Key
            file_type = re.findall('```(.*?)\n', str(rsp.content))[0]
            # summary = re.findall('File Summary:(.*?)', str(rsp.content))[0]
            content = re.findall(f'```{file_type}([\s\S]*?)```', str(rsp.content))[0]
            # info = f"\n## Step\n{context} \n\n ## Response\n{summary}\n"
            
            self._save(filename, content)
            return rsp

        output_class = ActionOutput.create_model_class("task", FINAL_OUTPUT_MAPPING)
        parsed_data = OutputParser.parse_data_with_mapping(info, FINAL_OUTPUT_MAPPING)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(info, instruct_content)

