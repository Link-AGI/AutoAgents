#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:50
@Author  : alexanderwu
@File    : __init__.py
@From    : https://github.com/geekan/MetaGPT/blob/main/metagpt/utils/__init__.py
"""


from .singleton import Singleton
from .token_counter import (
    TOKEN_COSTS,
    count_message_tokens,
    count_string_tokens,
)
