"""Tests for LatencyEvaluator."""

from agenteval.core.models import Trace
from agenteval.evaluators.latency import LatencyEvaluator


def make_trace(latency_ms: float) -> Trace:
    """Helper to create a trace with specified latency."""
    return Trace(
        agent_name="test",
        input="test input",
        output="test output",
        turns=[],
        total_cost_usd=0.0,
        total_latency_ms=latency_ms,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_under_limit():
    """Test that latency under limit passes."""
    trace = make_trace(500.0)
    evaluator = LatencyEvaluator()
    result = evaluator.evaluate(trace, {"max_latency_ms": 1000.0})
    assert result.passed is True
    assert result.score == 1.0


def test_over_limit():
    """Test that latency over limit fails."""
    trace = make_trace(1500.0)
    evaluator = LatencyEvaluator()
    result = evaluator.evaluate(trace, {"max_latency_ms": 1000.0})
    assert result.passed is False
    assert result.score < 1.0
    assert "1500" in result.reason or "1000" in result.reason


def test_no_criteria_passes():
    """Test that no criteria returns a pass."""
    trace = make_trace(100000.0)
    evaluator = LatencyEvaluator()
    result = evaluator.evaluate(trace, {})
    assert result.passed is True
    assert result.score == 1.0
