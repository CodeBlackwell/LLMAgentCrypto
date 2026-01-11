"""Trading strategy implementations."""

from .registry import register, get_strategy, list_strategies, get_strategy_info, get_all_strategies_info

# Import strategies to trigger registration
from . import random  # noqa: F401
from . import sentiment  # noqa: F401
from . import contrarian  # noqa: F401
from . import technical  # noqa: F401

__all__ = [
    "register",
    "get_strategy",
    "list_strategies",
    "get_strategy_info",
    "get_all_strategies_info",
]
