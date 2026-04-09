from datetime import datetime, timezone

from agenteval.core.models import (
    EvalResult,
    LLMCall,
    SuiteResult,
    TestResult,
    ToolCall,
    Trace,
    Turn,
)


def test_tool_call_creation():
    tc = ToolCall(
        name="search_flights",
        arguments={"destination": "Tokyo"},
        result={"flights": [{"id": "AA123"}]},
        timestamp=datetime.now(timezone.utc),
        duration_ms=150.0,
    )
    assert tc.name == "search_flights"
    assert tc.arguments["destination"] == "Tokyo"
    assert tc.duration_ms == 150.0


def test_llm_call_creation():
    call = LLMCall(
        provider="openai",
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        response="Hi there!",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.001,
        latency_ms=200.0,
        timestamp=datetime.now(timezone.utc),
    )
    assert call.provider == "openai"
    assert call.cost_usd == 0.001


def test_turn_creation():
    now = datetime.now(timezone.utc)
    turn = Turn(
        llm_calls=[
            LLMCall(
                provider="openai",
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
                response="ok",
                input_tokens=5,
                output_tokens=2,
                cost_usd=0.0005,
                latency_ms=100.0,
                timestamp=now,
            )
        ],
        tool_calls=[
            ToolCall(
                name="lookup",
                arguments={"id": "123"},
                result="found",
                timestamp=now,
                duration_ms=50.0,
            )
        ],
    )
    assert len(turn.llm_calls) == 1
    assert len(turn.tool_calls) == 1


def test_trace_creation_and_computed_fields():
    now = datetime.now(timezone.utc)
    trace = Trace(
        agent_name="test_agent",
        input="Book a flight",
        output="Flight booked: AA123",
        turns=[
            Turn(
                llm_calls=[
                    LLMCall(
                        provider="openai",
                        model="gpt-4o",
                        messages=[],
                        response="ok",
                        input_tokens=100,
                        output_tokens=50,
                        cost_usd=0.01,
                        latency_ms=500.0,
                        timestamp=now,
                    ),
                    LLMCall(
                        provider="openai",
                        model="gpt-4o",
                        messages=[],
                        response="done",
                        input_tokens=80,
                        output_tokens=30,
                        cost_usd=0.008,
                        latency_ms=300.0,
                        timestamp=now,
                    ),
                ],
                tool_calls=[
                    ToolCall(
                        name="search_flights",
                        arguments={},
                        result={},
                        timestamp=now,
                        duration_ms=200.0,
                    )
                ],
            )
        ],
        total_cost_usd=0.018,
        total_latency_ms=800.0,
        total_input_tokens=180,
        total_output_tokens=80,
        metadata={"env": "test"},
    )
    assert trace.agent_name == "test_agent"
    assert trace.turn_count == 1
    assert trace.all_tool_calls == ["search_flights"]
    assert trace.total_cost_usd == 0.018


def test_trace_serialization_roundtrip():
    trace = Trace(
        agent_name="test",
        input="hello",
        output="world",
        turns=[],
        total_cost_usd=0.0,
        total_latency_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        metadata={},
    )
    json_str = trace.model_dump_json()
    restored = Trace.model_validate_json(json_str)
    assert restored.agent_name == "test"
    assert restored.input == "hello"


def test_eval_result_creation():
    result = EvalResult(
        evaluator="tool_call",
        score=0.95,
        passed=True,
        reason="All expected tools were called",
        details={"expected": ["search"], "actual": ["search"]},
    )
    assert result.passed is True
    assert result.score == 0.95


def test_test_result_creation():
    result = TestResult(
        test_name="test_booking",
        trace=Trace(
            agent_name="test",
            input="x",
            output="y",
            turns=[],
            total_cost_usd=0.0,
            total_latency_ms=0.0,
            total_input_tokens=0,
            total_output_tokens=0,
            metadata={},
        ),
        eval_results=[],
        overall_score=0.9,
        passed=True,
        duration_ms=1500.0,
    )
    assert result.test_name == "test_booking"


def test_suite_result_creation():
    suite = SuiteResult(
        tests=[],
        total_passed=3,
        total_failed=1,
        avg_score=0.85,
        total_cost_usd=0.50,
        total_duration_ms=5000.0,
        generated_at=datetime.now(timezone.utc),
    )
    assert suite.total_passed == 3
    assert suite.total_failed == 1
