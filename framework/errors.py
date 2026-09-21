"""Exception types used across the framework."""
from __future__ import annotations


class FrameworkError(Exception):
    """Base class for all framework errors."""


class CsvFormatError(FrameworkError):
    """A CSV file is malformed (bad header, too many columns, ...)."""


class KeywordError(FrameworkError):
    """A keyword was used incorrectly (unknown keyword, bad locator, missing variable...)."""


class StepFailure(FrameworkError):
    """A step failed at run time. Carries enough context for reports and the healer agent."""

    def __init__(self, message: str, *, failure_dir=None):
        super().__init__(message)
        self.failure_dir = failure_dir
