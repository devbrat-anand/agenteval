from unittest.mock import MagicMock

from agenteval.core.models import Trace
from agenteval.evaluators.llm_judge import LLMJudgeEvaluator


def _make_trace() -> Trace:
    return Trace(
        agent_name="test",
        input="How do I return an item?",
        output="You can return items within 30 days by visiting our returns page.",
        turns=[],
        total_cost_usd=0.01,
        total_latency_ms=500,
        total_input_tokens=100,
        total_output_tokens=50,
        metadata={},
    )


def test_llm_judge_passes():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"helpful": 0.9, "accurate": 0.85}'

    evaluator = LLMJudgeEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace(),
        criteria={
            "criteria": {"helpful": "Was this helpful?", "accurate": "Was this accurate?"},
            "threshold": 0.7,
        },
    )
    assert result.passed is True
    assert result.score > 0.7


def test_llm_judge_fails():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"helpful": 0.3, "accurate": 0.4}'

    evaluator = LLMJudgeEvaluator(provider=mock_provider)
    result = evaluator.evaluate(
        _make_trace(),
        criteria={
            "criteria": {"helpful": "Was this helpful?", "accurate": "Was this accurate?"},
            "threshold": 0.7,
        },
    )
    assert result.passed is False


def test_llm_judge_name():
    evaluator = LLMJudgeEvaluator(provider=MagicMock())
    assert evaluator.name == "llm_judge"
