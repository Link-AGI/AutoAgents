# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/provider/openai_api.py
"""
import asyncio
import time
from functools import wraps
from typing import NamedTuple

import openai
import litellm

from autoagents.system.config import CONFIG
from autoagents.system.logs import logger
from autoagents.system.provider.base_gpt_api import BaseGPTAPI
from autoagents.system.utils.singleton import Singleton
from autoagents.system.utils.token_counter import (
    TOKEN_COSTS,
    count_message_tokens,
    count_string_tokens,
)


def retry(max_retries):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return await f(*args, **kwargs)
                except Exception:
                    if i == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** i)
        return wrapper
    return decorator


class RateLimiter:
    """Rate control class, each call goes through wait_if_needed, sleep if rate control is needed"""
    def __init__(self, rpm):
        self.last_call_time = 0
        self.interval = 1.1 * 60 / rpm  # Here 1.1 is used because even if the calls are made strictly according to time, they will still be QOS'd; consider switching to simple error retry later
        self.rpm = rpm

    def split_batches(self, batch):
        return [batch[i:i + self.rpm] for i in range(0, len(batch), self.rpm)]

    async def wait_if_needed(self, num_requests):
        current_time = time.time()
        elapsed_time = current_time - self.last_call_time

        if elapsed_time < self.interval * num_requests:
            remaining_time = self.interval * num_requests - elapsed_time
            logger.info(f"sleep {remaining_time}")
            await asyncio.sleep(remaining_time)

        self.last_call_time = time.time()


class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    total_budget: float


class CostManager(metaclass=Singleton):
    """计算使用接口的开销"""
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.total_budget = 0

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        cost = (
            prompt_tokens * TOKEN_COSTS[model]["prompt"]
            + completion_tokens * TOKEN_COSTS[model]["completion"]
        ) / 1000
        self.total_cost += cost
        logger.info(f"Total running cost: ${self.total_cost:.3f} | Max budget: ${CONFIG.max_budget:.3f} | "
                    f"Current cost: ${cost:.3f}, {prompt_tokens=}, {completion_tokens=}")
        CONFIG.total_cost = self.total_cost

    def get_total_prompt_tokens(self):
        """
        Get the total number of prompt tokens.

        Returns:
        int: The total number of prompt tokens.
        """
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        """
        Get the total number of completion tokens.

        Returns:
        int: The total number of completion tokens.
        """
        return self.total_completion_tokens

    def get_total_cost(self):
        """
        Get the total cost of API calls.

        Returns:
        float: The total cost of API calls.
        """
        return self.total_cost

    def get_costs(self) -> Costs:
        """获得所有开销"""
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost, self.total_budget)


class OpenAIGPTAPI(BaseGPTAPI, RateLimiter):
    """
    Check https://platform.openai.com/examples for examples
    """
    def __init__(self, proxy='', api_key=''):
        self.proxy = proxy
        self.api_key = api_key
        self.__init_openai(CONFIG)
        self.llm = openai
        self.stops = None
        self.model = CONFIG.openai_api_model
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openai(self, config):
        if self.proxy != '':
            openai.proxy = self.proxy
        else:
            litellm.api_key = config.openai_api_key
        
        if self.api_key != '':
            litellm.api_key = self.api_key
        else:
            litellm.api_key = config.openai_api_key
        
        if config.openai_api_base:
            litellm.api_base = config.openai_api_base
        if config.openai_api_type:
            litellm.api_type = config.openai_api_type
            litellm.api_version = config.openai_api_version
        self.rpm = int(config.get("RPM", 10))

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        response = await litellm.acompletion(
            **self._cons_kwargs(messages),
            stream=True
        )

        # create variables to collect the stream of chunks
        collected_chunks = []
        collected_messages = []
        # iterate through the stream of events
        async for chunk in response:
            collected_chunks.append(chunk)  # save the event response
            chunk_message = chunk['choices'][0]['delta']  # extract the message
            collected_messages.append(chunk_message)  # save the message
            if "content" in chunk_message:
                print(chunk_message["content"], end="")

        full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
        usage = self._calc_usage(messages, full_reply_content)
        self._update_costs(usage)
        return full_reply_content

    def _cons_kwargs(self, messages: list[dict]) -> dict:
        if CONFIG.openai_api_type == 'azure':
            kwargs = {
                "deployment_id": CONFIG.deployment_id,
                "messages": messages,
                "max_tokens": CONFIG.max_tokens_rsp,
                "n": 1,
                "stop": self.stops,
                "temperature": 0.3
            }
        else:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": CONFIG.max_tokens_rsp,
                "n": 1,
                "stop": self.stops,
                "temperature": 0.3
            }
        return kwargs

    async def _achat_completion(self, messages: list[dict]) -> dict:
        rsp = await self.llm.ChatCompletion.acreate(**self._cons_kwargs(messages))
        self._update_costs(rsp.get('usage'))
        return rsp

    def _chat_completion(self, messages: list[dict]) -> dict:
        rsp = self.llm.ChatCompletion.create(**self._cons_kwargs(messages))
        self._update_costs(rsp)
        return rsp

    def completion(self, messages: list[dict]) -> dict:
        # if isinstance(messages[0], Message):
        #     messages = self.messages_to_dict(messages)
        return self._chat_completion(messages)

    async def acompletion(self, messages: list[dict]) -> dict:
        # if isinstance(messages[0], Message):
        #     messages = self.messages_to_dict(messages)
        return await self._achat_completion(messages)

    @retry(max_retries=6)
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """when streaming, print each token in place."""
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)

    def _calc_usage(self, messages: list[dict], rsp: str) -> dict:
        usage = {}
        prompt_tokens = count_message_tokens(messages, self.model)
        completion_tokens = count_string_tokens(rsp, self.model)
        usage['prompt_tokens'] = prompt_tokens
        usage['completion_tokens'] = completion_tokens
        return usage

    async def acompletion_batch(self, batch: list[list[dict]]) -> list[dict]:
        """返回完整JSON"""
        split_batches = self.split_batches(batch)
        all_results = []

        for small_batch in split_batches:
            logger.info(small_batch)
            await self.wait_if_needed(len(small_batch))

            future = [self.acompletion(prompt) for prompt in small_batch]
            results = await asyncio.gather(*future)
            logger.info(results)
            all_results.extend(results)

        return all_results

    async def acompletion_batch_text(self, batch: list[list[dict]]) -> list[str]:
        """仅返回纯文本"""
        raw_results = await self.acompletion_batch(batch)
        results = []
        for idx, raw_result in enumerate(raw_results, start=1):
            result = self.get_choice_text(raw_result)
            results.append(result)
            logger.info(f"Result of task {idx}: {result}")
        return results

    def _update_costs(self, usage: dict):
        prompt_tokens = int(usage['prompt_tokens'])
        completion_tokens = int(usage['completion_tokens'])
        self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)

    def get_costs(self) -> Costs:
        return self._cost_manager.get_costs()
