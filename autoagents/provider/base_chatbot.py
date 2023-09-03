#!/usr/bin/env python
# -*- coding: utf-8 -*-
# https://github.com/geekan/MetaGPT/blob/main/metagpt/provider/base_chatbot.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseChatbot(ABC):
    """Abstract GPT class"""
    mode: str = "API"

    @abstractmethod
    def ask(self, msg: str) -> str:
        """Ask GPT a question and get an answer"""

    @abstractmethod
    def ask_batch(self, msgs: list) -> str:
        """Ask GPT multiple questions and get a series of answers"""

    @abstractmethod
    def ask_code(self, msgs: list) -> str:
        """Ask GPT multiple questions and get a piece of code"""
