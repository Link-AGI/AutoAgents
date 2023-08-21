#!/usr/bin/env python
# -*- coding: utf-8 -*-


from enum import Enum, auto


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = auto()
    DIRECT_GOOGLE = auto()
    SERPER_GOOGLE = auto()
    CUSTOM_ENGINE = auto()


class WebBrowserEngineType(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    CUSTOM = "custom"
