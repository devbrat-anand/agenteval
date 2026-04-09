"""Tests for CostEvaluator."""

from agenteval.core.models import Trace
from agenteval.evaluators.cost import CostEvaluator


def make_trace(cost_usd: float) -> Trace:
    """Helper to create a trace with specified cost."""
    return Trace(
        agent_name="test",
        input="test input",
        output="test output",
        turns=[],
        total_cost_usd=cost_usd,
        total_latency_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_under_budget():
    """Test that cost under budget passes."""
    trace = make_trace(0.05)
    evaluator = CostEvaluator()
    result = evaluator.evaluate(trace, {"max_cost_usd": 0.10})
    assert result.passed is True
    assert result.score == 1.0


def test_over_budget():
    """Test that cost over budget fails."""
    trace = make_trace(0.15)
    evaluator = CostEvaluator()
    result = evaluator.evaluate(trace, {"max_cost_usd": 0.10})
    assert result.passed is False
    assert result.score < 1.0
    assert "0.15" in result.reason or "0.1" in result.reason


def test_no_criteria_passes():
    """Test that no criteria returns a pass."""
    trace = make_trace(100.0)
    evaluator = CostEvaluator()
    result = evaluator.evaluate(trace, {})
    assert result.passed is True
    assert result.score == 1.0
