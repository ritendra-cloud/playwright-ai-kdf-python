"""pytest configuration: command-line options and shared fixtures."""
from __future__ import annotations

import pytest

from framework.config import load_settings
from framework.object_repository import ObjectRepository


def pytest_addoption(parser):
    group = parser.getgroup("kdf", "keyword-driven framework")
    group.addoption("--csv", action="append", default=[], metavar="PATH",
                    help="Run only this CSV file or folder (repeatable). Default: everything under test_cases/")
    group.addoption("--include-seed", action="store_true",
                    help="Also run test_cases/seed/ (the planner/generator starting-state tests)")


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def object_repo(settings):
    return ObjectRepository.load(settings.object_repo_dir)
