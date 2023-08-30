#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

from .action import Action
from .action_output import ActionOutput

from .requirement import Requirement
from .create_roles import CreateRoles
from .check_roles import CheckRoles
from .check_plans import CheckPlans

from .custom_action import CustomAction

# Predefined Actions
from .write_code import WriteCode
from .write_code_review import WriteCodeReview
from .project_management import AssignTasks, WriteTasks
from .design_api import WriteDesign
from .write_prd import WritePRD
from .search_and_summarize import SearchAndSummarize


class ActionType(Enum):
    """All types of Actions, used for indexing."""
    ADD_REQUIREMENT = Requirement
    CREATE_ROLES = CreateRoles
    OBSERVE_AGENTS = CheckRoles
    OBSERVE_PLANS = CheckPlans
    CUSTOM_ACTION = CustomAction

    SEARCH_AND_SUMMARIZE = SearchAndSummarize
    WRITE_DESIGN = WriteDesign
    WRITE_PRD = WritePRD
    WRITE_TASKS = WriteTasks
    ASSIGN_TASKS = AssignTasks
    WRTIE_CODE = WriteCode
    WRITE_CODE_REVIEW = WriteCodeReview