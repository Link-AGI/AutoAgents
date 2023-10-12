#!/usr/bin/env python
# -*- coding: utf-8 -*-
from autoagents.roles import Manager
from autoagents.explorer import Explorer


async def startup(idea: str, investment: float = 3.0, n_round: int = 10, task_id=None, 
                  llm_api_key: str=None, serpapi_key: str=None, proxy: str=None, alg_msg_queue: object=None):
    """Run a startup. Be a boss."""
    explorer = Explorer()
    explorer.hire([Manager(proxy=proxy, llm_api_key=llm_api_key, serpapi_api_key=serpapi_key)])
    explorer.invest(investment)
    await explorer.start_project(idea=idea, llm_api_key=llm_api_key, proxy=proxy, serpapi_key=serpapi_key, task_id=task_id, alg_msg_queue=alg_msg_queue)
    await explorer.run(n_round=n_round)