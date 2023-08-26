#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple
from autoagents.actions.action import Action
import re
import json

PROMPT_TEMPLATE = '''
-----
# Roles List
{context}

# Role
You are a ChatGPT executive observer expert skilled in identifying problem-solving plans and errors in the execution process. Your goal is to check if the created Expert Roles  following the requirements.

# Steps
1. You should first understand, analyze, and disassemble the human's problem.
2. You should check the Expert Roles. The valid JSON blob as follows:
{{{{
    "name": “ROLE NAME",
    "descriptions": "ROLE DESCRIPTONS",
    "prompt": "ROLE PROMPT",
    "tools": ["ROLE TOOL"],
    "steps": ["step1", "step2", "step3"],
}}}}
Specifically, the JSON should have a `name` key (the expert role name), a `descriptions` key (the description of the expert role's expertise domain), a `prompt` key (the prompt template required to call the expert role) and a `tools` key (with the name of the tools used by the expert role).
2.1 You should check if the planner creates the language expert role. If the language expert role not be created, you must add a language expert role that does not require any tools and is responsible for summarizing the result information of all steps.
2.2 You should check if the outputed Expert Roles conform to the valid JSON format. 
2.3 You should check if any roles use a new tool which not belongs to existing tools {tools}. Only existing tools {tools} can be used.
2.4 Create customized guide steps for each expert that leverages their areas of expertise to help them overcome their challenges or accomplish their goals.
2.4 A good prompt template should first explain the role it needs to play, its area of expertise, and the tools that can be used, and list the general process of solving the problem, but cannot contain any information about the problem. For example: "You are an expert of XXX. Your task is XXX. Respond to the human as helpfully and accurately as possible. Let's first understand the task or problem, and then extract information or values from the previous steps' responses, and finally construct your response. You have access to the following tools:".
3. Summarize the above inspection results. If there are any errors, you MUST re output the details of all expert roles in JSON blob format. Each JSON blob should only contain one expert role, and do NOT return a list of multiple expert roles. DO NOT FORGET to create the language expert role.

# Format example
Your final output should ALWAYS in the following format:
{format_example}

# IMPROTANT Attention
1. DO NOT forget to create the language expert role.
2. Only existing tools {tools} can be used for "tools" in JSON BLOB. If there are any tools not belongs to existings tools {tools}, you should delete them.
3. If there are no errors for the roles, you should output the original roles list in the section 'Revised Roles List'.
4. You should output the list of roles that includes all the revised roles correctly in the section ‘Revised Roles List’.
-----
'''

FORMAT_EXAMPLE = '''
---
## Observer
check if the created Expert Roles following the requirements.

## Errors 
you should always think about if there are any errors for created expert roles.

## Revised Roles List:
```
JSON BLOB 1,
JSON BLOB 2,
JSON BLOB 3,
```

## Anything UNCLEAR
We need ... how to start.
---
'''

OUTPUT_MAPPING = {
    "Revised Roles List": (str, ...),
    "Anything UNCLEAR": (str, ...),
}

TOOLS = 'tool: SearchAndSummarize, description: useful for when you need to answer unknown questions'

class CheckRoles(Action):
    def __init__(self, name="Check Roles", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context):
        context = re.findall('## Roles List:([\s\S]*?)##', str(context))[-1]
        prompt = PROMPT_TEMPLATE.format(context=context, format_example=FORMAT_EXAMPLE, tools=TOOLS)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)

        return rsp

