from datetime import datetime, timezone

from agenteval.core.models import LLMCall, Trace, Turn
from agenteval.evaluators.convergence import ConvergenceEvaluator


def _make_trace(output: str, turn_count: int = 1) -> Trace:
    now = datetime.now(timezone.utc)
    turns = [
        Turn(
            llm_calls=[
                LLMCall(
                    provider="openai",
                    model="gpt-4o",
                    messages=[],
                    response="step",
                    input_tokens=50,
                    output_tokens=25,
                    cost_usd=0.001,
                    latency_ms=100,
                    timestamp=now,
                )
            ],
            tool_calls=[],
        )
        for _ in range(turn_count)
    ]
    return Trace(
        agent_name="test",
        input="x",
        output=output,
        turns=turns,
        total_cost_usd=0.01 * turn_count,
        total_latency_ms=100 * turn_count,
        total_input_tokens=50 * turn_count,
        total_output_tokens=25 * turn_count,
        metadata={},
    )


def test_converged():
    evaluator = ConvergenceEvaluator()
    trace = _make_trace("Your flight AA123 is booked for March 10.", turn_count=3)
    result = evaluator.evaluate(trace, {})
    assert result.passed is True


def test_empty_output_not_converged():
    evaluator = ConvergenceEvaluator()
    trace = _make_trace("", turn_count=3)
    result = evaluator.evaluate(trace, {})
    assert result.passed is False


def test_error_output_not_converged():
    evaluator = ConvergenceEvaluator()
    trace = _make_trace(
        "I'm sorry, I encountered an error and cannot complete this task.", turn_count=3
    )
    result = evaluator.evaluate(trace, {"error_patterns": ["cannot complete", "error"]})
    assert result.passed is False


def test_max_turns_exceeded():
    evaluator = ConvergenceEvaluator()
    trace = _make_trace("partial result", turn_count=20)
    result = evaluator.evaluate(trace, {"max_turns": 10})
    assert result.passed is False
