#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@From    : MeteGPT
"""
from autoagents.actions import WritePRD, WriteTasks, WriteDesign
from autoagents.roles import Role

class ProductManager(Role):
    def __init__(self, watch_actions, name="Alice", profile="Product Manager", goal="Efficiently create a successful product",
                 constraints="", **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([WritePRD])
        self._watch(watch_actions)

class Architect(Role):
    """Architect: Listen to PRD, responsible for designing API, designing code files"""
    def __init__(self, watch_actions, name="Bob", profile="Architect", goal="Design a concise, usable, complete python system",
                 constraints="Try to specify good open source tools as much as possible", **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([WriteDesign])
        self._watch(watch_actions)

class ProjectManager(Role):
    def __init__(self, watch_actions, name="Eve", profile="Project Manager",
                 goal="Improve team efficiency and deliver with quality and quantity", constraints="", **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([WriteTasks])
        self._watch(watch_actions)
