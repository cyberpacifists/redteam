# -*- coding: utf-8 -*-
"""
Errors and exceptions
"""

class ActionExecutionError(Exception):
    """Raised when an Action execution by a worker fails"""

class ActionPreconditionError(Exception):
    """Raised when Action preconditions are not met"""

class ActionTimeoutError(Exception):
    """Raised when an Action execution times out"""
