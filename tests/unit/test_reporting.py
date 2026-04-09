import json
from datetime import datetime, timezone
from pathlib import Path

from agenteval.core.models import EvalResult, SuiteResult, TestResult, Trace
from agenteval.reporting.console import ConsoleReporter
from agenteval.reporting.html import HtmlReporter
from agenteval.reporting.json import JsonReporter


def _make_suite() -> SuiteResult:
    trace = Trace(
        agent_name="test",
        input="query",
        output="answer",
        turns=[],
        total_cost_usd=0.05,
        total_latency_ms=1200,
        total_input_tokens=200,
        total_output_tokens=100,
        metadata={},
    )
    return SuiteResult(
        tests=[
            TestResult(
                test_name="test_one",
                trace=trace,
                eval_results=[
                    EvalResult(
                        evaluator="tool_call", score=0.95, passed=True, reason="ok", details={}
                    ),
                    EvalResult(evaluator="cost", score=1.0, passed=True, reason="ok", details={}),
                ],
                overall_score=0.95,
                passed=True,
                duration_ms=500,
            ),
            TestResult(
                test_name="test_two",
                trace=trace,
                eval_results=[
                    EvalResult(
                        evaluator="hallucination",
                        score=0.4,
                        passed=False,
                        reason="ungrounded claim",
                        details={},
                    ),
                ],
                overall_score=0.4,
                passed=False,
                duration_ms=800,
            ),
        ],
        total_passed=1,
        total_failed=1,
        avg_score=0.675,
        total_cost_usd=0.10,
        total_duration_ms=1300,
        generated_at=datetime.now(timezone.utc),
    )


def test_console_reporter_produces_output(capsys):
    reporter = ConsoleReporter()
    suite = _make_suite()
    reporter.render(suite)
    captured = capsys.readouterr()
    assert "test_one" in captured.out
    assert "test_two" in captured.out
    assert "PASS" in captured.out or "pass" in captured.out.lower()
    assert "FAIL" in captured.out or "fail" in captured.out.lower()


def test_json_reporter_produces_valid_json(tmp_path: Path):
    reporter = JsonReporter()
    suite = _make_suite()
    output_file = tmp_path / "report.json"
    reporter.render(suite, output_path=output_file)
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["total_passed"] == 1
    assert data["total_failed"] == 1
    assert len(data["tests"]) == 2


def test_html_reporter_produces_html(tmp_path: Path):
    reporter = HtmlReporter()
    suite = _make_suite()
    output_file = tmp_path / "report.html"
    reporter.render(suite, output_path=output_file)
    assert output_file.exists()
    html = output_file.read_text()
    assert "<html" in html
    assert "test_one" in html
    assert "test_two" in html
