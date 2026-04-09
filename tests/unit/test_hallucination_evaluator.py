from datetime import datetime, timezone
from unittest.mock import MagicMock

from agenteval.core.models import ToolCall, Trace, Turn
from agenteval.evaluators.hallucination import HallucinationEvaluator


def _make_trace_with_tool_results(output: str, tool_results: list[dict]) -> Trace:
    now = datetime.now(timezone.utc)
    tool_calls = [
        ToolCall(
            name=tr.get("name", "tool"),
            arguments={},
            result=tr.get("result", ""),
            timestamp=now,
            duration_ms=50.0,
        )
        for tr in tool_results
    ]
    return Trace(
        agent_name="test",
        input="query",
        output=output,
        turns=[Turn(llm_calls=[], tool_calls=tool_calls)],
        total_cost_usd=0.01,
        total_latency_ms=500,
        total_input_tokens=100,
        total_output_tokens=50,
        metadata={},
    )


def test_hallucination_grounded_output():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = '{"grounding_score": 0.95, "ungrounded_claims": []}'

    evaluator = HallucinationEvaluator(provider=mock_provider)
    trace = _make_trace_with_tool_results(
        output="The order was placed on March 5th.",
        tool_results=[{"name": "lookup_order", "result": "Order placed: 2026-03-05"}],
    )
    result = evaluator.evaluate(trace, {"threshold": 0.9})
    assert result.passed is True
    assert result.score >= 0.9


def test_hallucination_ungrounded_output():
    mock_provider = MagicMock()
    mock_provider.judge.return_value = (
        '{"grounding_score": 0.3, "ungrounded_claims": ["free shipping claimed but not in data"]}'
    )

    evaluator = HallucinationEvaluator(provider=mock_provider)
    trace = _make_trace_with_tool_results(
        output="Your order ships for free!",
        tool_results=[{"name": "lookup_order", "result": "Shipping: $9.99"}],
    )
    result = evaluator.evaluate(trace, {"threshold": 0.9})
    assert result.passed is False


def test_hallucination_no_provider():
    evaluator = HallucinationEvaluator(provider=None)
    trace = _make_trace_with_tool_results("output", [])
    result = evaluator.evaluate(trace, {"threshold": 0.9})
    assert result.passed is False
    assert "provider" in result.reason.lower()
