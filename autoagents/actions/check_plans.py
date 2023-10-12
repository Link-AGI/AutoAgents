#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple
from .action import Action
import re

PROMPT_TEMPLATE = '''
-----
You are a ChatGPT executive observer expert skilled in identifying problem-solving plans and errors in the execution process. Your goal is to check if the Execution Plan following the requirements and give your improvement suggestions. You can refer to historical suggestions in the History section, but try not to repeat them.

# Question or Task
{context}

# Role List
{roles}

# Execution Plan
{plan}

# History
{history}

# Steps
You will check the Execution Plan by following these steps:
1. You should first understand, analyze, and disassemble the human's problem.
2. You should check if the execution plan meets the following requirements:
2.1. The execution plan should consist of multiple steps that solve the problem progressively. Make the plan as detailed as possible to ensure the accuracy and completeness of the task. You need to make sure that the summary of all the steps can answer the question or complete the task.
2.2. Each step should assign at least one expert role to carry it out. If a step involves multiple expert roles, you need to specify the contributions of each expert role and how they collaborate to produce integrated results. 
2.3. The description of each step should provide sufficient details and explain how the steps are connected to each other.
2.4. The description of each step must also include the expected output of that step and indicate what inputs are needed for the next step. The expected output of the current step and the required input for the next step must be consistent with each other. Sometimes, you may need to extract information or values before using them. Otherwise, the next step will lack the necessary input.
2.5. The final step should ALWAYS be an independent step that says `Language Expert: Based on the previous steps, please respond to the user's original question: XXX`.
3. Output a summary of the inspection results above. If you find any errors or have any suggestions, please state them clearly in the Suggestions section. If there are no errors or suggestions, you MUST write 'No Suggestions' in the Suggestions section.

# Format example
Your final output should ALWAYS in the following format:
{format_example}

# Attention
1. All expert roles can only use the existing tools {tools} for any expert role. They are not allowed to use any other tools. You CANNOT create any new tool for any expert role.
2. You can refer to historical suggestions and feedback in the History section but DO NOT repeat historical suggestions.
3. DO NOT ask any questions to the user or human. The final step should always be an independent step that says `Language Expert: Based on the previous steps, please provide a helpful, relevant, accurate, and detailed response to the user's original question: XXX`.
-----
'''

FORMAT_EXAMPLE = '''
---
## Thought
you should always think about if there are any errors or suggestions for the Execution Plan.

## Suggestions
1. ERROR1/SUGGESTION1
2. ERROR2/SUGGESTION2
2. ERROR3/SUGGESTION3
---
'''

OUTPUT_MAPPING = {
    "Suggestions": (str, ...),
}

# TOOLS = 'tool: SearchAndSummarize, description: useful for when you need to answer unknown questions'
TOOLS = 'None'


class CheckPlans(Action):
    def __init__(self, name="Check Plan", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, history=''):

        roles = re.findall('## Selected Roles List:([\s\S]*?)##', str(context))[-1]
        agents = re.findall('{[\s\S]*?}', roles)
        if len(agents) <= 0: roles = ''
        roles += re.findall('## Created Roles List:([\s\S]*?)##', str(context))[-1]
        plan = re.findall('## Execution Plan:([\s\S]*?)##', str(context))[-1]
        context = re.findall('## Question or Task:([\s\S]*?)##', str(context))[-1]
        prompt = PROMPT_TEMPLATE.format(context=context, plan=plan, roles=roles, format_example=FORMAT_EXAMPLE, history=history, tools=TOOLS)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)
        return rsp

