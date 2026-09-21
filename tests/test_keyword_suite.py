"""Runs every scenario found in test_cases/*.csv as one pytest test.

    pytest                                  # everything
    pytest -k TC001                         # one scenario by id
    pytest -m smoke                         # by tag (tags come from the CSV 'tags' column)
    pytest --csv test_cases/google_search.csv
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from framework.cli import discover_csv
from framework.config import load_settings
from framework.context import ExecutionContext
from framework.errors import StepFailure
from framework.executor import run_scenario
from framework.object_repository import ObjectRepository
from framework.reporting import write_results
from framework.validator import validate_files


def _csv_files(config, settings) -> list[Path]:
    requested = config.getoption("--csv")
    if not requested:
        return discover_csv(settings, include_seed=config.getoption("--include-seed"))
    files: list[Path] = []
    for item in requested:
        path = Path(item)
        files.extend(sorted(path.rglob("*.csv")) if path.is_dir() else [path])
    return files


def _marks(tags: tuple[str, ...]):
    marks = []
    for tag in tags:
        name = re.sub(r"\W", "_", tag)
        if name in ("skip", "fixme"):
            marks.append(pytest.mark.skip(reason=f"tagged '{name}' in the CSV"))
        marks.append(getattr(pytest.mark, name))
    return marks


def pytest_generate_tests(metafunc):
    if "scenario" not in metafunc.fixturenames:
        return
    settings = load_settings()
    repo = ObjectRepository.load(settings.object_repo_dir)
    scenarios, issues = validate_files(_csv_files(metafunc.config, settings), repo)
    errors = [str(i) for i in issues if i.level == "error"]
    if errors:
        raise pytest.UsageError("Invalid CSV test data:\n  " + "\n  ".join(errors))
    metafunc.parametrize(
        "scenario",
        [pytest.param(s, marks=_marks(s.tags), id=f"{s.source.stem}-{s.id}") for s in scenarios],
    )


@pytest.fixture(scope="session")
def results(settings):
    collected: list = []
    yield collected
    if collected:
        write_results(collected, settings.reports_dir)


def test_scenario(scenario, settings, object_repo, results):
    ctx = ExecutionContext(settings, object_repo, scenario_id=scenario.id)
    failure = None
    try:
        run_scenario(scenario, ctx, sink=results)
    except StepFailure as exc:
        failure = str(exc)
    if failure:                      # raised outside the except block -> no chained tracebacks
        pytest.fail(failure, pytrace=False)
