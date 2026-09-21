"""Static checks of CSV test cases - no browser needed. Used by the CLI, pytest and the agents."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .csv_reader import Scenario, read_scenarios
from .errors import CsvFormatError
from .keywords import check_arguments, get_keyword
from .object_repository import ObjectRepository

_NUMERIC_VALUE = {"validate_count", "validate_count_at_least", "wait"}


@dataclass(frozen=True)
class Issue:
    level: str          # error | warning
    file: Path
    line: int
    scenario: str
    message: str

    def __str__(self) -> str:
        where = f"{self.file}:{self.line}" if self.line else str(self.file)
        return f"{self.level.upper():7} {where} [{self.scenario or '-'}] {self.message}"


def validate_scenarios(scenarios: list[Scenario], repo: ObjectRepository) -> list[Issue]:
    issues: list[Issue] = []
    for sc in scenarios:
        def add(level, step_line, msg):
            issues.append(Issue(level, sc.source, step_line, sc.id, msg))

        for step in sc.steps:
            spec = get_keyword(step.keyword)
            if spec is None:
                add("error", step.line, f"unknown keyword '{step.keyword}' (see specs/keywords.md)")
                continue
            problem = check_arguments(spec, step.target, step.value)
            if problem:
                add("error", step.line, problem)
            if step.target.startswith("@") and "${" not in step.target:
                name = step.target[1:].strip()
                if name not in repo:
                    add("error", step.line, f"element '@{name}' is not in the object repository")
            if spec.name in _NUMERIC_VALUE and step.value and "${" not in step.value:
                if not re.fullmatch(r"\d+(\.\d+)?", step.value):
                    add("error", step.line, f"'{spec.name}' needs a number in 'value', got '{step.value}'")
        names = {spec.name for spec in (get_keyword(st.keyword) for st in sc.steps) if spec}
        if "open_browser" not in names:
            add("warning", sc.steps[0].line, "no open_browser step (a browser is launched automatically)")
        if "close_browser" not in names:
            add("warning", sc.steps[-1].line, "no close_browser step (the browser is closed automatically)")
    return issues


def validate_files(paths: list[Path], repo: ObjectRepository) -> tuple[list[Scenario], list[Issue]]:
    scenarios: list[Scenario] = []
    issues: list[Issue] = []
    for path in paths:
        try:
            parsed = read_scenarios(path)
        except CsvFormatError as exc:
            issues.append(Issue("error", path, 0, "", str(exc)))
            continue
        scenarios.extend(parsed)
        issues.extend(validate_scenarios(parsed, repo))
    return scenarios, issues
