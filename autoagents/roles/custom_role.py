#!/usr/bin/env python
# -*- coding: utf-8 -*-

from autoagents.roles import Role
from autoagents.actions import CustomAction

class CustomRole(Role):
    def __init__(self, role_prompt, steps, tool, watch_actions,
                name="CustomRole", 
                profile="CustomeRole", 
                goal="Efficiently to finish the tasks",
                constraints="",
                serpapi_key=None,
                **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        class_name = name.replace(' ', '_')+'_Action'
        Action_object = type(class_name, (CustomAction,), {"role_prompt":role_prompt, "steps":steps, "tool":tool, "serpapi_key":str(serpapi_key)})
        self.init_actions = Action_object
        self._init_actions([self.init_actions])
        self._watch(watch_actions)

