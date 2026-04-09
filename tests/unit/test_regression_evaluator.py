from agenteval.core.models import Trace
from agenteval.evaluators.regression import RegressionEvaluator


def _make_trace(cost: float = 0.05, output: str = "result") -> Trace:
    return Trace(
        agent_name="test",
        input="x",
        output=output,
        turns=[],
        total_cost_usd=cost,
        total_latency_ms=500,
        total_input_tokens=100,
        total_output_tokens=50,
        metadata={},
    )


def test_no_regression():
    evaluator = RegressionEvaluator()
    current = _make_trace(cost=0.05)
    baseline = _make_trace(cost=0.05)
    result = evaluator.evaluate(
        current,
        {
            "baseline_trace": baseline,
            "baseline_score": 0.9,
            "current_score": 0.88,
            "threshold": 0.05,
        },
    )
    assert result.passed is True


def test_detects_score_regression():
    evaluator = RegressionEvaluator()
    current = _make_trace(cost=0.05)
    baseline = _make_trace(cost=0.05)
    result = evaluator.evaluate(
        current,
        {
            "baseline_trace": baseline,
            "baseline_score": 0.9,
            "current_score": 0.7,
            "threshold": 0.05,
        },
    )
    assert result.passed is False


def test_detects_cost_regression():
    evaluator = RegressionEvaluator()
    current = _make_trace(cost=0.50)
    baseline = _make_trace(cost=0.05)
    result = evaluator.evaluate(
        current,
        {
            "baseline_trace": baseline,
            "baseline_score": 0.9,
            "current_score": 0.9,
            "threshold": 0.05,
            "max_cost_increase": 2.0,
        },
    )
    assert result.passed is False


def test_no_baseline_passes():
    evaluator = RegressionEvaluator()
    result = evaluator.evaluate(_make_trace(), {})
    assert result.passed is True
