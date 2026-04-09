from unittest.mock import MagicMock

from agenteval.core.models import Trace
from agenteval.evaluators.guardrail import GuardrailEvaluator


def _make_trace(output: str) -> Trace:
    return Trace(
        agent_name="test",
        input="x",
        output=output,
        turns=[],
        total_cost_usd=0,
        total_latency_ms=0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_within_scope():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = (
        '{"in_scope": true, "toxic": false, "explanation": "On topic"}'
    )

    evaluator = GuardrailEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace("Your order will arrive by Friday."),
        {"scope": "customer support, orders, shipping"},
    )
    assert result.passed is True


def test_out_of_scope():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = (
        '{"in_scope": false, "toxic": false, "explanation": "Response about politics"}'
    )

    evaluator = GuardrailEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace("I think the current president is doing a great job."),
        {"scope": "customer support, orders, shipping"},
    )
    assert result.passed is False


def test_toxic_content():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = (
        '{"in_scope": true, "toxic": true, "explanation": "Contains inappropriate language"}'
    )

    evaluator = GuardrailEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace("You're an idiot for ordering this."),
        {"scope": "customer support"},
    )
    assert result.passed is False


def test_no_scope_skips_scope_check():
    evaluator = GuardrailEvaluator(provider=None)
    result = evaluator.evaluate(_make_trace("Normal response"), {})
    assert result.passed is True


def test_no_provider_with_scope_fails():
    evaluator = GuardrailEvaluator(provider=None)
    result = evaluator.evaluate(
        _make_trace("output"),
        {"scope": "customer support"},
    )
    assert result.passed is False
