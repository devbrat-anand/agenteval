from agenteval.interceptors.anthropic import AnthropicInterceptor


def test_has_correct_name():
    interceptor = AnthropicInterceptor()
    assert interceptor.name == "anthropic"
    assert interceptor.package_marker == "anthropic"


def test_record_call():
    interceptor = AnthropicInterceptor()
    interceptor.activate()
    interceptor._record_call(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "test"}],
        response_content="hello",
        input_tokens=100,
        output_tokens=50,
        latency_ms=200.0,
    )
    calls = interceptor.get_calls()
    assert len(calls) == 1
    assert calls[0].provider == "anthropic"
    assert calls[0].cost_usd > 0
    interceptor.deactivate()
