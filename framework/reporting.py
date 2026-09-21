"""Run results and failure bundles.

When a step fails the framework writes reports/failures/<file>_<test_id>/ containing:
    failure.md   what failed, the resolved locator, the error, the page URL/title, and the
                 page's accessibility snapshot (this is what the healer agent reads)
    failure.png  screenshot at the moment of failure
    aria.yml     accessibility snapshot of the page
    trace.zip    Playwright trace (open with: python -m playwright show-trace <file>)
"""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .context import ExecutionContext, safe_name
from .csv_reader import Scenario, Step


@dataclass
class StepResult:
    index: int
    keyword: str
    target: str
    value: str
    line: int
    status: str = "not_run"          # passed | failed | not_run
    duration_s: float = 0.0
    error: str = ""


@dataclass
class ScenarioResult:
    id: str
    name: str
    source: str
    status: str = "not_run"
    duration_s: float = 0.0
    steps: list[StepResult] = field(default_factory=list)
    failure_dir: str = ""


def failure_dir_for(ctx: ExecutionContext, scenario: Scenario) -> Path:
    return ctx.settings.reports_dir / "failures" / safe_name(f"{scenario.source.stem}_{scenario.id}")


def clear_failure_dir(ctx: ExecutionContext, scenario: Scenario) -> None:
    """Remove stale failure bundles so the healer never reads an outdated one."""
    shutil.rmtree(failure_dir_for(ctx, scenario), ignore_errors=True)


def write_failure_bundle(
    ctx: ExecutionContext, scenario: Scenario, index: int, step: Step,
    target: str, value: str, exc: BaseException,
) -> Path | None:
    """Best-effort: a problem while reporting must never hide the original failure."""
    try:
        folder = failure_dir_for(ctx, scenario)
        folder.mkdir(parents=True, exist_ok=True)
        page = ctx.page_if_open
        url = title = aria = ""
        if page is not None:
            try:
                url, title = page.url, page.title()
            except Exception:  # noqa: BLE001
                pass
            try:
                page.screenshot(path=str(folder / "failure.png"))
            except Exception:  # noqa: BLE001
                pass
            try:
                aria = page.locator("body").aria_snapshot()
                (folder / "aria.yml").write_text(aria, encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        error_text = str(exc).strip()
        lines = [
            f"# Failure: {scenario.id} - {scenario.name}",
            "",
            f"- **CSV file:** `{scenario.source}` (line {step.line})",
            f"- **Step:** #{index} `{step.keyword}`",
            f"- **Target (as written):** `{step.target}`",
            f"- **Target (after variables):** `{target}`",
        ]
        if ctx.last_locator and ctx.last_locator != target:
            lines.append(f"- **Locator used:** `{ctx.last_locator}`")
        if target.startswith("@"):
            try:
                lines.append(f"- **Object repository entry:** `{ctx.repo.get(target[1:])}`")
            except Exception:  # noqa: BLE001
                pass
        masked = "****" if _is_sensitive(step.keyword) else value
        lines += [
            f"- **Value (after variables):** `{masked}`",
            f"- **Description:** {step.description or '-'}",
            f"- **Page URL:** {url or '(browser not open)'}",
            f"- **Page title:** {title or '-'}",
            f"- **Exception:** `{type(exc).__name__}`",
            "",
            "## Error",
            "```",
            error_text[:4000],
            "```",
            "",
            "## Artifacts",
            "- `failure.png` screenshot, `aria.yml` accessibility snapshot, `trace.zip` (open with: python -m playwright show-trace trace.zip)",
        ]
        if aria:
            snippet = "\n".join(aria.splitlines()[:250])
            lines += ["", "## Accessibility snapshot at failure (first 250 lines)", "```yaml", snippet, "```"]
        (folder / "failure.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return folder
    except Exception:  # noqa: BLE001
        return None


def _is_sensitive(keyword_name: str) -> bool:
    from .keywords import get_keyword
    spec = get_keyword(keyword_name)
    return bool(spec and spec.sensitive)


def write_results(results: list[ScenarioResult], reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "results.json"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": sum(r.status == "passed" for r in results),
        "failed": sum(r.status == "failed" for r in results),
        "scenarios": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
