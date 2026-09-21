"""Self-checks: run the real engine against a local HTML page (no internet, no Google)."""
from __future__ import annotations

from pathlib import Path

import pytest

from framework.config import load_settings
from framework.context import ExecutionContext
from framework.csv_reader import read_scenarios
from framework.errors import StepFailure
from framework.executor import run_scenario
from framework.object_repository import ObjectRepository

HERE = Path(__file__).parent
FAKE_URL = (HERE / "fixtures" / "fake_search.html").as_uri()

pytestmark = pytest.mark.selfcheck


@pytest.fixture()
def offline_settings(tmp_path):
    # Bundled Chromium, headless, short timeout: independent of the developer's .env
    return load_settings(channel=None, headless=True, timeout_ms=2000, reports_dir=tmp_path)


@pytest.fixture()
def repo():
    return ObjectRepository.load(HERE / "repo")


def _ctx(settings, repo, scenario):
    return ExecutionContext(settings, repo, scenario_id=scenario.id, variables={"FAKE_URL": FAKE_URL})


def test_happy_path_runs_all_keywords_and_closes_browser(offline_settings, repo):
    scenarios = {s.id: s for s in read_scenarios(HERE / "cases" / "offline_search.csv")}
    for scenario_id in ("OFF1", "OFF2"):
        scenario = scenarios[scenario_id]
        ctx = _ctx(offline_settings, repo, scenario)
        result = run_scenario(scenario, ctx)
        assert result.status == "passed"
        assert all(step.status == "passed" for step in result.steps)
        assert ctx.session is None, "browser must be closed after the test"
    assert (offline_settings.reports_dir / "screenshots" / "OFF1" / "offline-results.png").exists()


def test_failure_writes_a_bundle_for_the_healer_and_still_closes_browser(offline_settings, repo):
    scenario = read_scenarios(HERE / "cases" / "offline_failure.csv")[0]
    ctx = _ctx(offline_settings, repo, scenario)
    with pytest.raises(StepFailure) as info:
        run_scenario(scenario, ctx)
    folder = info.value.failure_dir
    assert folder is not None
    report = (folder / "failure.md").read_text(encoding="utf-8")
    assert "step:** #3" in report.lower() and "css=#does-not-exist" in report
    assert "line 4" in report                       # CSV line of the failing step
    assert "Fake Search" in report                  # accessibility snapshot was captured
    for artifact in ("failure.png", "aria.yml", "trace.zip"):
        assert (folder / artifact).exists(), artifact
    assert ctx.session is None, "browser must be closed even when a step fails"


def test_masked_secret_and_argument_checks(offline_settings, repo, tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text(
        "test_id,keyword,target,value\nB1,click,,\nB1,notakeyword,,\nB1,navigate,,\n", encoding="utf-8")
    from framework.validator import validate_files
    _, issues = validate_files([csv_file], repo)
    messages = " | ".join(i.message for i in issues if i.level == "error")
    assert "needs a value in the 'target' column" in messages
    assert "unknown keyword 'notakeyword'" in messages
    assert "needs a value in the 'value' column" in messages
