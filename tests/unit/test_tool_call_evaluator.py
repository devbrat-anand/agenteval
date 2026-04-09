"""Tests for ToolCallEvaluator."""

from datetime import datetime

from agenteval.core.models import ToolCall, Trace, Turn
from agenteval.evaluators.tool_call import ToolCallEvaluator


def make_tool_call(name: str) -> ToolCall:
    """Helper to create a tool call."""
    return ToolCall(
        name=name,
        arguments={},
        result=None,
        timestamp=datetime.now(),
        duration_ms=100.0,
    )


def make_trace(tool_names: list[str]) -> Trace:
    """Helper to create a trace with tool calls in a single turn."""
    return Trace(
        agent_name="test",
        input="test input",
        output="test output",
        turns=[Turn(tool_calls=[make_tool_call(name) for name in tool_names])],
        total_cost_usd=0.0,
        total_latency_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_tool_called_pass():
    """Test that expected_tools passes when all tools are called."""
    trace = make_trace(["search", "calculate", "format"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"expected_tools": ["search", "calculate"]})
    assert result.passed is True
    assert result.score == 1.0


def test_tool_called_fail():
    """Test that expected_tools fails when a tool is missing."""
    trace = make_trace(["search", "format"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"expected_tools": ["search", "calculate"]})
    assert result.passed is False
    assert result.score < 1.0
    assert "calculate" in result.reason


def test_tool_call_order_pass():
    """Test that expected_order passes when tools are called in correct order."""
    trace = make_trace(["search", "process", "calculate", "format"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"expected_order": ["search", "calculate"]})
    assert result.passed is True
    assert result.score == 1.0


def test_tool_call_order_fail():
    """Test that expected_order fails when tools are out of order."""
    trace = make_trace(["calculate", "search", "format"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"expected_order": ["search", "calculate"]})
    assert result.passed is False
    assert result.score < 1.0
    assert "order" in result.reason.lower()


def test_forbidden_tools_pass():
    """Test that forbidden_tools passes when no forbidden tools are called."""
    trace = make_trace(["search", "calculate"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"forbidden_tools": ["delete", "modify"]})
    assert result.passed is True
    assert result.score == 1.0


def test_forbidden_tools_fail():
    """Test that forbidden_tools fails when a forbidden tool is called."""
    trace = make_trace(["search", "delete", "calculate"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {"forbidden_tools": ["delete", "modify"]})
    assert result.passed is False
    assert result.score == 0.0
    assert "delete" in result.reason


def test_no_criteria_passes():
    """Test that no criteria returns a pass."""
    trace = make_trace(["search", "calculate"])
    evaluator = ToolCallEvaluator()
    result = evaluator.evaluate(trace, {})
    assert result.passed is True
    assert result.score == 1.0
