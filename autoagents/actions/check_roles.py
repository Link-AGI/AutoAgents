#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple
from .action import Action
import re
import json

PROMPT_TEMPLATE = '''
-----
You are a ChatGPT executive observer expert skilled in identifying problem-solving plans and errors in the execution process. Your goal is to check if the created Expert Roles following the requirements and give your improvement suggestions. You can refer to historical suggestions in the History section, but try not to repeat them.

# Question or Task
{question}

# Existing Expert Roles
{existing_roles}

# Selected Roles List
{selected_roles}

# Created Roles List
{created_roles}

# History
{history}

# Steps
You will check the selected roles list and created roles list by following these steps:
1. You should first understand, analyze, and break down the human's problem/task.
2. According to the problem, existing expert roles and the toolset ({tools}), you should check the selected expert roles.
2.1. You should make sure that the selected expert roles can help you solve the problem effectively and efficiently.
2.2. You should make sure that the selected expert roles meet the requirements of the problem and have cooperative or dependent relationships with each other. 
2.3. You should make sure that the JSON blob of each selected expert role contains its original information, such as name, description, and requirements.
3. According to the problem, existing expert roles and the toolset ({tools}), you should check the new expert roles that you have created.
3.1. You should avoid creating any new expert role that has duplicate functions with any existing expert role. If there are duplicates, you should use the existing expert role instead.
3.2. You should include the following information for each new expert role: a name, a detailed description of their area of expertise, a list of tools that they need to use, some suggestions for executing the task, and a prompt template for calling them.
3.3. You should assign a clear and specific domain of expertise to each new expert role based on the content of the problem. You should not let one expert role do too many tasks or have vague responsibilities. The description of their area of expertise should be detailed enough to let them know what they are capable of doing. 
3.4. You should give a meaningful and expressive name to each new expert role based on their domain of expertise. The name should reflect the characteristics and functions of the expert role. 
3.5. You should state a clear and concise goal for each new expert role based on their domain of expertise. The goal must indicate the primary responsibility or objective that the expert role aims to achieve. 
3.6. You should specify any limitations or principles that each new expert role must adhere to when performing actions. These are called constraints and they must be consistent with the problem requirements and the domain of expertise. 
3.7. You should select the appropriate tools that each new expert role needs to use from the existing tool set. Each new expert role can have multiple tools or no tool at all, depending on their functions and needs. You should never create any new tool and only use the existing ones.
3.8. You should provide some helpful suggestions for each new expert role to execute the task effectively and efficiently. The suggestions should include but not limited to a clear output format, extraction of relevant information from previous steps, and guidance for execution steps.
3.9. You should create a prompt template for calling each new expert role according to its name, description, goal, constraints, tools and suggestions. A good prompt template should first explain the role it needs to play (name), its area of expertise (description), the primary responsibility or objective that it aims to achieve (goal), any limitations or principles that it must adhere to when performing actions (constraints), and some helpful suggestions for executing the task (suggestions). The prompt must follow this format: “You are [description], named [name]. Your goal is [goal], and your constraints are [constraints]. You could follow these execution suggestions: [suggestions].”.
3.10. You should always have a language expert role who does not require any tools and is responsible for summarizing the results of all steps in natural language. 
3.11. You should follow the JSON blob format for creating new expert roles. Specifically, The JSON of new expert roles should have a `name` key (the expert role name), a `description` key (the description of the expert role's expertise domain), a `tools` key (with the name of the tools used by the expert role), a `suggestions` key (some suggestions for each agent to execute the task), and a `prompt` key (the prompt template required to call the expert role). Each JSON blob should only contain one expert role, and do NOT return a list of multiple expert roles. Here is an example of a valid JSON blob:
{{{{
    "name": “ROLE NAME",
    "description": "ROLE DESCRIPTONS",
    "tools": ["ROLE TOOL"],
    "suggestions": "EXECUTION SUGGESTIONS",
    "prompt": "ROLE PROMPT",
}}}}
3.12. You need to check if the tool contains other tools that are not in the tool ({tools}), and if they do, they should be removed.
4. Output a summary of the inspection results above. If you find any errors or have any suggestions, please state them clearly in the Suggestions section. If there are no errors or suggestions, you MUST write 'No Suggestions' in the Suggestions section.

# Format example
Your final output should ALWAYS in the following format:
{format_example}

# Attention
1. Please adhere to the requirements of the existing expert roles.
2. DO NOT forget to create the language expert role.
3. You can refer to historical suggestions and feedback in the History section but DO NOT repeat historical suggestions.
4. All expert roles can only use the existing tools ({tools}) for any expert role. They are not allowed to use any other tools. You CANNOT create any new tool for any expert role.
5. DO NOT ask any questions to the user or human. The final step should always be an independent step that says `Language Expert: Based on the previous steps, please provide a helpful, relevant, accurate, and detailed response to the user's original question: XXX`.
-----
'''

FORMAT_EXAMPLE = '''
---
## Thought
you should always think about if there are any errors or suggestions for selected and created expert roles.

## Suggestions
1. ERROR1/SUGGESTION1
2. ERROR2/SUGGESTION2
2. ERROR3/SUGGESTION3
---
'''

OUTPUT_MAPPING = {
    "Suggestions": (str, ...),
}

# TOOLS = '['
# for item in TOOLS_LIST:
#     TOOLS += '(Tool:' + item['toolname'] + '. Description:' + item['description'] + '),'
# TOOLS += ']'

# TOOLS = 'tool: SearchAndSummarize, description: useful for when you need to answer unknown questions'
TOOLS = 'None'


class CheckRoles(Action):
    def __init__(self, name="Check Roles", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, history=''):
        from autoagents.roles import ROLES_LIST
        question = re.findall('## Question or Task:([\s\S]*?)##', str(context))[0]
        created_roles = re.findall('## Created Roles List:([\s\S]*?)##', str(context))[0]
        selected_roles = re.findall('## Selected Roles List:([\s\S]*?)##', str(context))[0]
        
        prompt = PROMPT_TEMPLATE.format(question=question, history=history, existing_roles=ROLES_LIST, created_roles=created_roles, selected_roles=selected_roles, format_example=FORMAT_EXAMPLE, tools=TOOLS)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)

        return rsp

