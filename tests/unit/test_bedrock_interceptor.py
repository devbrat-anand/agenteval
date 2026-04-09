from agenteval.interceptors.bedrock import BedrockInterceptor


def test_has_correct_name():
    interceptor = BedrockInterceptor()
    assert interceptor.name == "bedrock"
    assert interceptor.package_marker == "boto3"


def test_activate_and_deactivate():
    interceptor = BedrockInterceptor()
    interceptor.activate()
    assert interceptor._active is True
    interceptor.deactivate()
    assert interceptor._active is False


def test_record_call():
    interceptor = BedrockInterceptor()
    interceptor.activate()
    interceptor._record_call(
        model="anthropic.claude-sonnet-4-6-v1",
        messages=[{"role": "user", "content": "test"}],
        response_content="hello",
        input_tokens=100,
        output_tokens=50,
        latency_ms=200.0,
    )
    calls = interceptor.get_calls()
    assert len(calls) == 1
    assert calls[0].provider == "bedrock"
    assert calls[0].model == "anthropic.claude-sonnet-4-6-v1"
    assert calls[0].cost_usd > 0
    interceptor.clear()
    assert len(interceptor.get_calls()) == 0
    interceptor.deactivate()
