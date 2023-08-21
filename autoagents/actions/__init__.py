#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

from .action import Action
from .action_output import ActionOutput
from .requirement import Requirement
from .create_roles import CreateRoles
from .search_and_summarize import SearchAndSummarize
from .check_roles import CheckRoles
from .check_plans import CheckPlans
from .custom_action import CustomAction

class ActionType(Enum):
    """All types of Actions, used for indexing."""
    ADD_REQUIREMENT = Requirement
    CREATE_ROLES = CreateRoles
    OBSERVE_AGENTS = CheckRoles
    OBSERVE_PLANS = CheckPlans
    CUSTOM_ACTION = CustomAction
    SEARCH_AND_SUMMARIZE = SearchAndSummarize
