from unittest.mock import MagicMock

from agenteval.core.eval_model import EvalModel
from agenteval.core.models import EvalResult, Trace


def _make_trace() -> Trace:
    return Trace(
        agent_name="test",
        input="question",
        output="answer",
        turns=[],
        total_cost_usd=0.01,
        total_latency_ms=500,
        total_input_tokens=100,
        total_output_tokens=50,
        metadata={},
    )


def test_eval_model_judge():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"helpful": 0.9, "accurate": 0.8}'

    model = EvalModel(provider=mock_provider)
    trace = _make_trace()
    verdict = model.judge(
        trace,
        criteria={"helpful": "Was this helpful?", "accurate": "Was this accurate?"},
        threshold=0.7,
    )
    assert isinstance(verdict, EvalResult)
    mock_provider.judge.assert_called_once()


def test_eval_model_judge_with_scores():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"helpful": 0.9, "accurate": 0.8}'

    model = EvalModel(provider=mock_provider)
    trace = _make_trace()
    verdict = model.judge(
        trace,
        criteria={"helpful": "Was this helpful?", "accurate": "Was this accurate?"},
        threshold=0.7,
    )
    assert verdict.passed is True
    assert "helpful" in verdict.details.get("scores", {})


def test_eval_model_judge_fails_below_threshold():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"helpful": 0.3, "accurate": 0.4}'

    model = EvalModel(provider=mock_provider)
    trace = _make_trace()
    verdict = model.judge(
        trace,
        criteria={"helpful": "Was this helpful?", "accurate": "Was this accurate?"},
        threshold=0.7,
    )
    assert verdict.passed is False
