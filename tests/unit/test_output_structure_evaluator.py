"""Tests for OutputStructureEvaluator."""

from agenteval.core.models import Trace
from agenteval.evaluators.output_structure import OutputStructureEvaluator


def make_trace(output: str) -> Trace:
    """Helper to create a trace with specified output."""
    return Trace(
        agent_name="test",
        input="test input",
        output=output,
        turns=[],
        total_cost_usd=0.0,
        total_latency_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_contains_pass():
    """Test that contains check passes when all keywords present."""
    trace = make_trace("The quick brown fox jumps over the lazy dog")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"contains": ["quick", "fox", "lazy"]})
    assert result.passed is True
    assert result.score == 1.0


def test_contains_fail():
    """Test that contains check fails when keyword missing."""
    trace = make_trace("The quick brown fox")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"contains": ["quick", "fox", "elephant"]})
    assert result.passed is False
    assert result.score < 1.0
    assert "elephant" in result.reason.lower()


def test_excludes_pass():
    """Test that excludes check passes when forbidden keywords absent."""
    trace = make_trace("The quick brown fox")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"excludes": ["error", "failed", "bug"]})
    assert result.passed is True
    assert result.score == 1.0


def test_excludes_fail():
    """Test that excludes check fails when forbidden keyword present."""
    trace = make_trace("The operation failed with an error")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"excludes": ["error", "failed", "bug"]})
    assert result.passed is False
    assert result.score == 0.0
    assert "failed" in result.reason.lower() or "error" in result.reason.lower()


def test_regex_match_pass():
    """Test that regex check passes when pattern matches."""
    trace = make_trace("Total cost: $12.34")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"regex": r"\$\d+\.\d{2}"})
    assert result.passed is True
    assert result.score == 1.0


def test_regex_match_fail():
    """Test that regex check fails when pattern doesn't match."""
    trace = make_trace("Total cost: 12 dollars")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {"regex": r"\$\d+\.\d{2}"})
    assert result.passed is False
    assert result.score == 0.0


def test_json_schema_pass():
    """Test that JSON schema validation passes for valid JSON."""
    trace = make_trace('{"name": "John", "age": 30}')
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(
        trace,
        {"json_schema": {"type": "object", "required": ["name", "age"]}},
    )
    assert result.passed is True
    assert result.score == 1.0


def test_json_schema_fail():
    """Test that JSON schema validation fails for invalid JSON."""
    trace = make_trace('{"name": "John"}')
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(
        trace,
        {"json_schema": {"type": "object", "required": ["name", "age"]}},
    )
    assert result.passed is False
    assert result.score == 0.0


def test_no_criteria_passes():
    """Test that no criteria returns a pass."""
    trace = make_trace("Any output")
    evaluator = OutputStructureEvaluator()
    result = evaluator.evaluate(trace, {})
    assert result.passed is True
    assert result.score == 1.0
