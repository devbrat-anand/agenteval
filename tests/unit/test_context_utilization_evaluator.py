from datetime import datetime, timezone
from unittest.mock import MagicMock

from agenteval.core.models import ToolCall, Trace, Turn
from agenteval.evaluators.context_utilization import ContextUtilizationEvaluator


def _make_trace_with_context(output: str, tool_results: list[str]) -> Trace:
    now = datetime.now(timezone.utc)
    tool_calls = [
        ToolCall(name="retrieve", arguments={}, result=r, timestamp=now, duration_ms=50)
        for r in tool_results
    ]
    return Trace(
        agent_name="test",
        input="query",
        output=output,
        turns=[Turn(llm_calls=[], tool_calls=tool_calls)],
        total_cost_usd=0,
        total_latency_ms=0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )


def test_good_utilization():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"utilization_score": 0.85}'

    evaluator = ContextUtilizationEvaluator(provider=mock_provider)
    trace = _make_trace_with_context(
        output="Based on the return policy, you have 30 days.",
        tool_results=["Return policy: 30 day window for all items."],
    )
    result = evaluator.evaluate(trace, {"threshold": 0.6})
    assert result.passed is True


def test_poor_utilization():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"utilization_score": 0.2}'

    evaluator = ContextUtilizationEvaluator(provider=mock_provider)
    trace = _make_trace_with_context(
        output="I'm not sure about the return policy.",
        tool_results=["Return policy: 30 day window for all items."],
    )
    result = evaluator.evaluate(trace, {"threshold": 0.6})
    assert result.passed is False


def test_no_context_passes():
    evaluator = ContextUtilizationEvaluator(provider=MagicMock())
    trace = _make_trace_with_context("output", [])
    result = evaluator.evaluate(trace, {"threshold": 0.6})
    assert result.passed is True
