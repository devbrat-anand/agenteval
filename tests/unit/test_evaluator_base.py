"""Tests for evaluator base interface and registry."""

import pytest

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator, EvaluatorRegistry


class DummyEvaluator(Evaluator):
    """Test evaluator for unit tests."""

    name = "dummy"

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        """Always passes."""
        return EvalResult(
            evaluator=self.name,
            score=1.0,
            passed=True,
            reason="Always passes",
            details={},
        )


def test_evaluator_interface():
    """Test that evaluator can be instantiated and called."""
    evaluator = DummyEvaluator()
    trace = Trace(
        agent_name="test",
        input="x",
        output="y",
        turns=[],
        total_cost_usd=0,
        total_latency_ms=0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )
    result = evaluator.evaluate(trace, {})
    assert result.passed is True
    assert result.score == 1.0


def test_registry_register_and_list():
    """Test registering evaluators and listing them."""
    registry = EvaluatorRegistry()
    registry.register(DummyEvaluator)
    assert "dummy" in registry.available()


def test_registry_create():
    """Test creating evaluator instances from registry."""
    registry = EvaluatorRegistry()
    registry.register(DummyEvaluator)
    evaluator = registry.create("dummy")
    assert isinstance(evaluator, DummyEvaluator)


def test_registry_create_unknown_raises():
    """Test that creating unknown evaluator raises KeyError."""
    registry = EvaluatorRegistry()
    with pytest.raises(KeyError, match="Unknown evaluator: nonexistent"):
        registry.create("nonexistent")
