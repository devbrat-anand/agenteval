from agenteval.interceptors.pricing import PricingEngine


def test_get_cost_openai() -> None:
    engine = PricingEngine()
    cost = engine.compute_cost(
        provider="openai",
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost > 0
    assert isinstance(cost, float)


def test_get_cost_unknown_provider_returns_zero() -> None:
    engine = PricingEngine()
    cost = engine.compute_cost(
        provider="nonexistent-provider",
        model="nonexistent-model-xyz",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost == 0.0


def test_get_cost_unknown_model_uses_default() -> None:
    engine = PricingEngine()
    cost = engine.compute_cost(
        provider="openai",
        model="future-model-xyz",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost > 0  # should use _default pricing


def test_get_cost_bedrock() -> None:
    engine = PricingEngine()
    cost = engine.compute_cost(
        provider="bedrock",
        model="anthropic.claude-sonnet-4-6-v1",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost > 0


def test_pricing_table_has_major_providers() -> None:
    engine = PricingEngine()
    providers = engine.available_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "bedrock" in providers
