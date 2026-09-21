"""Importing this package registers every built-in keyword."""
from . import browser_keywords, data_keywords, interaction_keywords, validation_keywords  # noqa: F401
from .registry import KeywordSpec, all_keywords, check_arguments, get_keyword, keyword, normalize  # noqa: F401
