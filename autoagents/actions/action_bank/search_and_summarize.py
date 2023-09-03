#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/actions/search_and_summarize.py
"""
import time

from autoagents.actions import Action
from autoagents.system.config import Config
from autoagents.system.logs import logger
from autoagents.system.schema import Message
from autoagents.system.tools.search_engine import SearchEngine

SEARCH_AND_SUMMARIZE_SYSTEM = """### Requirements
1. Please summarize the latest dialogue based on the reference information (secondary) and dialogue history (primary). Do not include text that is irrelevant to the conversation.
- The context is for reference only. If it is irrelevant to the user's search request history, please reduce its reference and usage.
2. If there are citable links in the context, annotate them in the main text in the format [main text](citation link). If there are none in the context, do not write links.
3. The reply should be graceful, clear, non-repetitive, smoothly written, and of moderate length, in {LANG}.

### Dialogue History (For example)
A: MLOps competitors

### Current Question (For example)
A: MLOps competitors

### Current Reply (For example)
1. Alteryx Designer: <desc> etc. if any
2. Matlab: ditto
3. IBM SPSS Statistics
4. RapidMiner Studio
5. DataRobot AI Platform
6. Databricks Lakehouse Platform
7. Amazon SageMaker
8. Dataiku
"""

SEARCH_AND_SUMMARIZE_SYSTEM_EN_US = SEARCH_AND_SUMMARIZE_SYSTEM.format(LANG='en-us')

SEARCH_AND_SUMMARIZE_PROMPT = """
### Reference Information
{CONTEXT}

### Dialogue History
{QUERY_HISTORY}
{QUERY}

### Current Question
{QUERY}

### Current Reply: Based on the information, please write the reply to the Question


"""


SEARCH_AND_SUMMARIZE_SALES_SYSTEM = """## Requirements
1. Please summarize the latest dialogue based on the reference information (secondary) and dialogue history (primary). Do not include text that is irrelevant to the conversation.
- The context is for reference only. If it is irrelevant to the user's search request history, please reduce its reference and usage.
2. If there are citable links in the context, annotate them in the main text in the format [main text](citation link). If there are none in the context, do not write links.
3. The reply should be graceful, clear, non-repetitive, smoothly written, and of moderate length, in Simplified Chinese.

# Example
## Reference Information
...

## Dialogue History
user: Which facial cleanser is good for oily skin?
Salesperson: Hello, for oily skin, it is suggested to choose a product that can deeply cleanse, control oil, and is gentle and skin-friendly. According to customer feedback and market reputation, the following facial cleansers are recommended:...
user: Do you have any by L'Oreal?
> Salesperson: ...

## Ideal Answer
Yes, I've selected the following for you:
1. L'Oreal Men's Facial Cleanser: Oil control, anti-acne, balance of water and oil, pore purification, effectively against blackheads, deep exfoliation, refuse oil shine. Dense foam, not tight after washing.
2. L'Oreal Age Perfect Hydrating Cleanser: Added with sodium cocoyl glycinate and Centella Asiatica, two effective ingredients, it can deeply cleanse, tighten the skin, gentle and not tight.
"""

SEARCH_AND_SUMMARIZE_SALES_PROMPT = """
## Reference Information
{CONTEXT}

## Dialogue History
{QUERY_HISTORY}
{QUERY}
> {ROLE}: 

"""

SEARCH_FOOD = """
# User Search Request
What are some delicious foods in Xiamen?

# Requirements
You are a member of a professional butler team and will provide helpful suggestions:
1. Please summarize the user's search request based on the context and avoid including unrelated text.
2. Use [main text](reference link) in markdown format to **naturally annotate** 3-5 textual elements (such as product words or similar text sections) within the main text for easy navigation.
3. The response should be elegant, clear, **without any repetition of text**, smoothly written, and of moderate length.
"""


class SearchAndSummarize(Action):
    def __init__(self, name="", context=None, llm=None, engine=None, search_func=None, serpapi_api_key=None):
        self.config = Config()
        self.serpapi_api_key = serpapi_api_key
        self.engine = engine or self.config.search_engine
        self.search_engine = SearchEngine(self.engine, run_func=search_func, serpapi_api_key=serpapi_api_key)
        self.result = ""
        super().__init__(name, context, llm, serpapi_api_key)

    async def run(self, context: list[Message], system_text=SEARCH_AND_SUMMARIZE_SYSTEM) -> str:
        no_serpapi = not self.config.serpapi_api_key or 'YOUR_API_KEY' == self.config.serpapi_api_key
        no_serper = not self.config.serper_api_key or 'YOUR_API_KEY' == self.config.serper_api_key
        no_google = not self.config.google_api_key or 'YOUR_API_KEY' == self.config.google_api_key
        no_self_serpapi = self.serpapi_api_key is None

        if no_serpapi and no_google and no_serper and no_self_serpapi:
            logger.warning('Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature')
            return ""
        
        query = context[-1].content
        # logger.debug(query)
        try_count = 0
        while True:
            try:
                rsp = await self.search_engine.run(query)
                break
            except ValueError as e:
                try_count += 1
                if try_count >= 3:
                    # Retry 3 times to fail
                    raise e
                time.sleep(1)

        self.result = rsp
        if not rsp:
            logger.error('empty rsp...')
            return ""
        # logger.info(rsp)

        system_prompt = [system_text]

        prompt = SEARCH_AND_SUMMARIZE_PROMPT.format(
            # PREFIX = self.prefix,
            ROLE=self.profile,
            CONTEXT=rsp,
            QUERY_HISTORY='\n'.join([str(i) for i in context[:-1]]),
            QUERY=str(context[-1])
        )
        result = await self._aask(prompt, system_prompt)
        logger.debug(prompt)
        logger.debug(result)
        return result
