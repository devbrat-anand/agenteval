"""pytest plugin registration for agenteval."""

from __future__ import annotations

import time
from pathlib import Path

import pytest  # noqa: TC002

from agenteval.pytest_plugin.assertions import patch_trace_assertions
from agenteval.pytest_plugin.fixtures import (
    agent_runner,  # noqa: F401
    eval_model,  # noqa: F401
)

_collected_results: list[dict] = []


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "agenteval(cost_budget): agenteval test configuration")
    config.addinivalue_line("markers", "regression(baseline): regression test against baseline")
    config.addinivalue_line("markers", "slow: mark test as slow (requires LLM judge)")
    config.addinivalue_line("markers", "evaluators(*names): run specific evaluators only")
    patch_trace_assertions()
    _collected_results.clear()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("agenteval", "agenteval agent testing")
    group.addoption(
        "--agenteval-fail-under",
        type=float,
        default=None,
        help="Fail if average eval score is below this threshold (0.0-1.0)",
    )
    group.addoption(
        "--agenteval-max-cost",
        type=float,
        default=None,
        help="Fail if total eval cost exceeds this amount (USD)",
    )
    group.addoption(
        "--agenteval-eval-provider",
        type=str,
        default=None,
        help="Eval provider: ollama, openai, bedrock (overrides config)",
    )
    group.addoption(
        "--agenteval-eval-model",
        type=str,
        default=None,
        help="Eval model name (overrides config)",
    )
    group.addoption(
        "--agenteval-report",
        type=str,
        default=None,
        help="Report format: console, html, json",
    )
    group.addoption(
        "--agenteval-report-dir",
        type=str,
        default="agenteval-reports",
        help="Report output directory",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> None:  # type: ignore[misc,return]
    from agenteval.pytest_plugin._collector import (
        get_and_clear_eval_results,
        get_and_clear_traces,
    )

    get_and_clear_traces()
    get_and_clear_eval_results()

    start = time.monotonic()
    outcome = yield
    duration_ms = (time.monotonic() - start) * 1000

    if not any(item.iter_markers("agenteval")):
        get_and_clear_traces()
        get_and_clear_eval_results()
        return

    traces = get_and_clear_traces()
    eval_results = get_and_clear_eval_results()
    if not traces:
        return

    passed = outcome.excinfo is None

    for trace in traces:
        _collected_results.append(
            {
                "test_name": item.nodeid,
                "trace": trace,
                "eval_results": eval_results,
                "passed": passed,
                "duration_ms": duration_ms,
            }
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    report_format = session.config.getoption("--agenteval-report", default=None)
    if not report_format or not _collected_results:
        return

    from datetime import datetime, timezone

    from agenteval.core.models import SuiteResult, TestResult

    test_results = []
    for entry in _collected_results:
        eval_results = entry.get("eval_results", [])
        if eval_results:
            overall_score = sum(r.score for r in eval_results) / len(eval_results)
        else:
            overall_score = 1.0 if entry["passed"] else 0.0
        tr = TestResult(
            test_name=entry["test_name"],
            trace=entry["trace"],
            eval_results=eval_results,
            overall_score=round(overall_score, 4),
            passed=entry["passed"],
            duration_ms=entry["duration_ms"],
        )
        test_results.append(tr)

    total_passed = sum(1 for t in test_results if t.passed)
    total_failed = len(test_results) - total_passed
    avg_score = (
        sum(t.overall_score for t in test_results) / len(test_results) if test_results else 0.0
    )
    total_cost = sum(t.trace.total_cost_usd for t in test_results)
    total_duration = sum(t.duration_ms for t in test_results)

    suite = SuiteResult(
        tests=test_results,
        total_passed=total_passed,
        total_failed=total_failed,
        avg_score=avg_score,
        total_cost_usd=total_cost,
        total_duration_ms=total_duration,
        generated_at=datetime.now(tz=timezone.utc),
    )

    report_dir = Path(
        session.config.getoption("--agenteval-report-dir", default="agenteval-reports")
    )
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")

    from agenteval.reporting import ConsoleReporter, HtmlReporter, JsonReporter

    reporters = {
        "console": (ConsoleReporter, None),
        "html": (HtmlReporter, report_dir / f"report_{timestamp}.html"),
        "json": (JsonReporter, report_dir / f"report_{timestamp}.json"),
    }

    for fmt in report_format.split(","):
        fmt = fmt.strip().lower()
        if fmt in reporters:
            cls, output_path = reporters[fmt]
            cls().render(suite, output_path=output_path)

    _collected_results.clear()
