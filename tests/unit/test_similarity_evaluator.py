from unittest.mock import MagicMock

from agenteval.core.models import Trace
from agenteval.evaluators.similarity import SimilarityEvaluator


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


def test_similarity_high_score():
    mock_provider = MagicMock()
    mock_provider.embed.return_value = [1.0, 0.0, 0.0]

    evaluator = SimilarityEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace("Items can be returned within 30 days"),
        {"reference": "Items can be returned within 30 days", "threshold": 0.8},
    )
    assert result.passed is True
    assert result.score >= 0.99


def test_similarity_low_score():
    mock_provider = MagicMock()
    call_count = [0]

    def side_effect(text: str) -> list[float]:
        call_count[0] += 1
        if call_count[0] == 1:
            return [1.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0]

    mock_provider.embed.side_effect = side_effect

    evaluator = SimilarityEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace("Something completely different"),
        {"reference": "Items can be returned within 30 days", "threshold": 0.8},
    )
    assert result.passed is False
    assert result.score < 0.1


def test_similarity_no_provider():
    evaluator = SimilarityEvaluator(provider=None)
    result = evaluator.evaluate(
        _make_trace("output"),
        {"reference": "reference", "threshold": 0.8},
    )
    assert result.passed is False


def test_similarity_no_reference():
    evaluator = SimilarityEvaluator(provider=MagicMock())
    result = evaluator.evaluate(_make_trace("output"), {"threshold": 0.8})
    assert result.passed is True
