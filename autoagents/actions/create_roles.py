#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Tuple

from autoagents.logs import logger
from autoagents.actions.action import Action
from .search_and_summarize import SearchAndSummarize, SEARCH_AND_SUMMARIZE_SYSTEM_EN_US
# from .tools import TOOLS_LIST

PROMPT_TEMPLATE = '''
-----
# Question or Task
{context}

# Search Information
{search_information}

# Existing Expert Roles
{existing_roles}

# Role
You are a manager and an expert-level ChatGPT prompt engineer with expertise in multiple fields; the goal is to break down tasks by creating multi LLM agents, give a role list, and analyze role dependencies.

# Steps
You will come up with solutions for any task or problem by following these steps:
1. You should first understand, analyze, and disassemble the human's problem.
2. According to the problem, existing expert roles and the toolset ({tools}), you will choose existing expert roles needed to solve the problem on the basis of serving as an expert level ChatGPT prompt engineer and planner with expertise in multiple fields, so as to better develop a problem solving plan to provide the best answer. You should create roles following these principles:
2.1. Fully utilize existing expert roles to solve problems.
2.2. Please follow the requirements of the existing expert roles. Ensure that existing expert roles with cooperative or dependent relationships are selected.
2.3. You MUST output the details of selected existing expert roles in JSON blob format. Specifically, The JSON of the selected existing expert role can output its original information.
3. According to the problem, existing expert roles and the toolset ({tools}), you will create additional expert roles needed to solve the problem on the basis of serving as an expert level ChatGPT prompt engineer and planner with expertise in multiple fields, so as to better develop a problem solving plan to provide the best answer. You should create roles following these principles:
3.1. The newly created expert role cannot have duplicate functions with existing expert roles. If there are duplicates, there is no need to create this role.
3.2. Each new expert role includes a name, a detailed description of their area of expertise, prompt templates, and available tools.
3.3. Determine the number of new expert roles to be added and their areas of expertise based on the content of the problem. Please make sure each expert has a clear responsibility and do not let one expert do too many jobs. The description of their area of expertise should be detailed so that the role understands what he is capable of doing.
3.4. You must add a language expert role who does not require any tools and is responsible for summarizing the result information of all steps.
3.5. Determine the names of each new expert role based on their areas of expertise.
3.6. Determine the list of tools that each new expert needs to use based on the existing tool set. Each new expert role can have multiple tools or do not have any tool. You should NEVER create any new tool and only existing tools can be used.
3.7. Generate the prompt template required for calling each new expert role according to its area of expertise and tools. A good prompt template should first explain the role it needs to play, its area of expertise, and the tools that can be used, and list the general process of solving the problem, but cannot contain any information about the problem. For example: "You are an expert of XXX. Your task is XXX. Respond to the human as helpfully and accurately as possible. Let's first understand the task or problem, and then extract information or values from the previous steps' responses, and finally construct your response. You have access to the following tools:".
3.8. Create customized guide steps for each expert that leverages their areas of expertise to help them overcome their challenges or accomplish their goals.
3.9. You MUST output the details of created new expert roles in JSON blob format. Specifically, The JSON of new expert roles should have a `name` key (the expert role name), a `description` key (the description of the expert role's expertise domain), a `prompt` key (the prompt template required to call the expert role) and a `tools` key (with the name of the tools used by the expert role). Each JSON blob should only contain one expert role, and do NOT return a list of multiple expert roles. Here is an example of a valid JSON blob:
{{{{
    "name": “ROLE NAME",
    "description": "ROLE DESCRIPTONS",
    "prompt": "ROLE PROMPT",
    "tools": ["ROLE TOOL"],
    "steps": ["step1", "step2", "step3"],
}}}}
4. Finally, based on the content of the problem and the expert roles, provide a detailed execution plan with the required steps to solve the problem.
4.1. The execution plan should be divided into multiple steps to solve the problem step by step. Each step should have at least one expert role to execute. If a step involves multiple expert roles, you need to describe the contributions of each expert role and how they collaborate to produce comprehensive results. 
4.2  The step description should provide as much detail as possible and explain how the steps are related to each other. The step description must also include the expected output of the current step and specify what inputs are required for the next step. Expected output of the current step and required input for the next step must match each other.
4.3. NEVER guess the result of a step.
4.4. Make the plan as detailed as possible to accurately complete the task.
4.5. Output the execution plan as a numbered list of steps. Please indicate the name of the expert role used at the beginning of the step. 
4.6. The final step should always be an independent step 'XXX: Given the above steps taken, please respond to the users original question: XXX' by the language expert role. At the end of your plan, say '<END_OF_PLAN>'

# Format example
Your final output should ALWAYS in the following format:
{format_example}

# Attention
1. Please follow the requirements of the existing expert roles.
2. Only existing tools can be used. You CAN NOT create any new tool for any expert role.
3. Sometimes, you should extract information or values before using it. Otherwise, next step will lack the necessary input.
4. Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.
5. You can only use the existing tools {tools} for any expert role. You are not allowed to use any other tools. DO NOT forget to create the language expert role.
-----
'''

FORMAT_EXAMPLE = '''
---
## Thought 
you should always think about what type of expert roles needs to be created and the key steps needed to accomplish the tasks.

## Question or Task:
the input question you must answer / the input task you must finish

## Selected Roles List:
```
JSON BLOB 1,
JSON BLOB 2,
JSON BLOB 3
```

## Created Roles List:
```
JSON BLOB 1,
JSON BLOB 2,
JSON BLOB 3
```

## Execution Plan:
1. ROLE 1: STEP 1
2. ROLE 2: STEP 2
2. ROLE 3: STEP 3

## Anything UNCLEAR
We need ... how to start.
---
'''

OUTPUT_MAPPING = {
    "Selected Roles List": (str, ...),
    "Created Roles List": (str, ...),
    "Execution Plan": (str, ...),
    "Anything UNCLEAR": (str, ...),
}

# TOOLS = '['
# for item in TOOLS_LIST:
#     TOOLS += '(Tool:' + item['toolname'] + '. Description:' + item['description'] + '),'
# TOOLS += ']'
TOOLS = 'tool: SearchAndSummarize, description: useful for when you need to answer unknown questions'


class CreateRoles(Action):

    def __init__(self, name="CreateRolesTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context):
        # sas = SearchAndSummarize()
        sas = SearchAndSummarize(serpapi_api_key=self.serpapi_api_key, llm=self.llm)
        rsp = await sas.run(context=context, system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
        rsp = ""
        info = f"## Search Results\n{sas.result}\n\n## Search Summary\n{rsp}"

        from autoagents.roles import ROLES_LIST
        prompt = PROMPT_TEMPLATE.format(context=context, format_example=FORMAT_EXAMPLE, existing_roles=ROLES_LIST, search_information=info, tools=TOOLS)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
