from agenteval.interceptors.openai import OpenAIInterceptor


def test_interceptor_has_correct_name() -> None:
    interceptor = OpenAIInterceptor()
    assert interceptor.name == "openai"


def test_activate_and_deactivate() -> None:
    interceptor = OpenAIInterceptor()
    interceptor.activate()
    assert interceptor._active is True
    interceptor.deactivate()
    assert interceptor._active is False


def test_clear_removes_captured_calls() -> None:
    interceptor = OpenAIInterceptor()
    interceptor.activate()
    interceptor._record_call(
        model="gpt-4o",
        messages=[{"role": "user", "content": "test"}],
        response_content="hello",
        input_tokens=10,
        output_tokens=5,
        latency_ms=100.0,
    )
    assert len(interceptor.get_calls()) == 1
    interceptor.clear()
    assert len(interceptor.get_calls()) == 0
    interceptor.deactivate()


def test_record_call_creates_llm_call() -> None:
    interceptor = OpenAIInterceptor()
    interceptor.activate()
    interceptor._record_call(
        model="gpt-4o",
        messages=[{"role": "user", "content": "test"}],
        response_content="hello",
        input_tokens=100,
        output_tokens=50,
        latency_ms=200.0,
    )
    calls = interceptor.get_calls()
    assert len(calls) == 1
    assert calls[0].provider == "openai"
    assert calls[0].model == "gpt-4o"
    assert calls[0].input_tokens == 100
    assert calls[0].output_tokens == 50
    assert calls[0].cost_usd > 0
    interceptor.deactivate()
