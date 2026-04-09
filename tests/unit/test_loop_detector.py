"""Tests for LoopDetectorEvaluator."""

from datetime import datetime

from agenteval.core.models import ToolCall, Trace, Turn
from agenteval.evaluators.loop_detector import LoopDetectorEvaluator


def make_tool_call(name: str) -> ToolCall:
    """Helper to create a tool call."""
    return ToolCall(
        name=name,
        arguments={},
        result=None,
        timestamp=datetime.now(),
        duration_ms=100.0,
    )


def make_trace_with_turns(turns_tools: list[list[str]]) -> Trace:
    """Helper to create a trace with multiple turns, each with tool calls."""
    turns = [Turn(tool_calls=[make_tool_call(name) for name in tools]) for tools in turns_tools]
    return Trace(
        agent_name="test",
        input="test input",
        output="test output",
        turns=turns,
        total_cost_usd=0.0,
        total_latency_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_no_loop():
    """Test that varied tool usage passes."""
    trace = make_trace_with_turns(
        [
            ["search", "calculate"],
            ["format", "validate"],
            ["output"],
        ]
    )
    evaluator = LoopDetectorEvaluator()
    result = evaluator.evaluate(trace, {"max_repeats": 3})
    assert result.passed is True
    assert result.score == 1.0


def test_detects_tool_loop():
    """Test detection of consecutive repeated tool calls."""
    trace = make_trace_with_turns(
        [
            ["search", "search", "search", "search"],  # 4 consecutive repeats
        ]
    )
    evaluator = LoopDetectorEvaluator()
    result = evaluator.evaluate(trace, {"max_repeats": 3})
    assert result.passed is False
    assert result.score < 1.0
    assert "search" in result.reason.lower()


def test_detects_turn_pattern_loop():
    """Test detection of repeated turn patterns."""
    trace = make_trace_with_turns(
        [
            ["search", "calculate"],
            ["search", "calculate"],
            ["search", "calculate"],
            ["search", "calculate"],  # Same pattern 4 times
        ]
    )
    evaluator = LoopDetectorEvaluator()
    result = evaluator.evaluate(trace, {"max_repeats": 3})
    assert result.passed is False
    assert result.score < 1.0
    assert "pattern" in result.reason.lower()


def test_no_criteria_uses_default():
    """Test that default max_repeats=3 is used when not specified."""
    trace = make_trace_with_turns(
        [
            ["search", "search", "search", "search"],  # 4 consecutive repeats
        ]
    )
    evaluator = LoopDetectorEvaluator()
    result = evaluator.evaluate(trace, {})  # No criteria
    assert result.passed is False  # Should still detect with default
