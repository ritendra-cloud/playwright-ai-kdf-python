"""Runs one scenario: resolve variables -> look up keyword -> execute -> report."""
from __future__ import annotations

import logging
import time

from .context import ExecutionContext
from .csv_reader import Scenario
from .errors import KeywordError, StepFailure
from .keywords import check_arguments, get_keyword
from .reporting import (
    ScenarioResult, StepResult, clear_failure_dir, failure_dir_for, write_failure_bundle,
)

log = logging.getLogger("kdf")


def run_scenario(
    scenario: Scenario, ctx: ExecutionContext, sink: list[ScenarioResult] | None = None
) -> ScenarioResult:
    """Execute every step in order; stop at the first failure.

    The browser is ALWAYS closed afterwards (pass or fail). On failure a bundle with a screenshot,
    accessibility snapshot, trace and failure.md is written and StepFailure is raised.
    """
    result = ScenarioResult(scenario.id, scenario.name, str(scenario.source))
    if sink is not None:
        sink.append(result)
    clear_failure_dir(ctx, scenario)
    log.info("")
    log.info("[%s] %s  (%d steps)", scenario.id, scenario.name, len(scenario.steps))
    started = time.perf_counter()
    failure_dir = None
    try:
        for index, step in enumerate(scenario.steps, start=1):
            spec = get_keyword(step.keyword)
            record = StepResult(index, step.keyword, step.target, step.value, step.line)
            result.steps.append(record)
            t0 = time.perf_counter()
            target = value = ""
            try:
                if spec is None:
                    raise KeywordError(f"Unknown keyword '{step.keyword}'. Run: python -m framework.cli keywords")
                target, value = ctx.resolve(step.target), ctx.resolve(step.value)
                problem = check_arguments(spec, target, value)
                if problem:
                    raise KeywordError(problem)
                shown = "****" if spec.sensitive else value
                log.info("  %02d %-26s %-34s %s", index, spec.name, target, shown)
                spec.func(ctx, target, value)
                record.status = "passed"
            except Exception as exc:  # noqa: BLE001 - every failure gets the same treatment
                record.status = "failed"
                record.error = str(exc).strip().splitlines()[0][:300] if str(exc).strip() else type(exc).__name__
                failure_dir = write_failure_bundle(ctx, scenario, index, step, target, value, exc)
                result.status = "failed"
                result.failure_dir = str(failure_dir or "")
                log.info("      FAILED: %s", record.error)
                raise StepFailure(
                    f"[{scenario.id}] step {index} '{step.keyword}' failed "
                    f"({scenario.source.name}, line {step.line})\n"
                    f"  {record.error}\n"
                    f"  details: {failure_dir / 'failure.md' if failure_dir else '(no bundle written)'}",
                    failure_dir=failure_dir,
                ) from exc
            finally:
                record.duration_s = round(time.perf_counter() - t0, 3)
        result.status = "passed"
    finally:
        result.duration_s = round(time.perf_counter() - started, 3)
        trace = (failure_dir_for(ctx, scenario) / "trace.zip") if result.status == "failed" else None
        ctx.close_browser(trace_path=trace)   # guaranteed cleanup
    log.info("[%s] PASSED (%.1fs)", scenario.id, result.duration_s)
    return result
