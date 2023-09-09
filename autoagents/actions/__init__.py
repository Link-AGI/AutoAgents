#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

from .action import Action, ActionOutput

from .create_roles import CreateRoles
from .check_roles import CheckRoles
from .check_plans import CheckPlans
from .custom_action import CustomAction
from .steps import NextAction

# Predefined Actions
from .action_bank.requirement import Requirement
from .action_bank.write_code import WriteCode
from .action_bank.write_code_review import WriteCodeReview
from .action_bank.project_management import AssignTasks, WriteTasks
from .action_bank.design_api import WriteDesign
from .action_bank.write_prd import WritePRD
from .action_bank.search_and_summarize import SearchAndSummarize
