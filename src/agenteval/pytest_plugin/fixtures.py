"""pytest fixtures for agenteval."""

from __future__ import annotations

import pytest

from agenteval.core.config import load_config
from agenteval.core.eval_model import EvalModel
from agenteval.core.runner import AgentRunner
from agenteval.providers.base import default_provider_registry


@pytest.fixture
def agent_runner() -> AgentRunner:
    return AgentRunner()


@pytest.fixture
def eval_model(request: pytest.FixtureRequest) -> EvalModel:
    config = load_config()

    cli_provider = request.config.getoption("--agenteval-eval-provider", default=None)
    cli_model = request.config.getoption("--agenteval-eval-model", default=None)

    eval_provider = cli_provider or config.eval_provider

    kwargs: dict[str, object] = {}
    if cli_model:
        kwargs["model"] = cli_model
    elif not cli_provider or cli_provider == config.eval_provider:
        kwargs["model"] = config.eval_model
    if eval_provider == "openai":
        if config.openai_base_url:
            kwargs["base_url"] = config.openai_base_url
        if config.openai_api_key:
            kwargs["api_key"] = config.openai_api_key
    elif eval_provider == "bedrock":
        if config.aws_profile:
            kwargs["profile"] = config.aws_profile
        if config.aws_region:
            kwargs["region"] = config.aws_region

    try:
        provider = default_provider_registry.create(eval_provider, **kwargs)
    except (KeyError, Exception) as err:
        if cli_provider:
            raise RuntimeError(
                f"Eval provider '{cli_provider}' not available"
            ) from err
        for fallback in ["ollama", "openai", "bedrock"]:
            try:
                fallback_kwargs: dict[str, object] = {}
                if fallback == "openai":
                    if config.openai_base_url:
                        fallback_kwargs["base_url"] = config.openai_base_url
                    if config.openai_api_key:
                        fallback_kwargs["api_key"] = config.openai_api_key
                elif fallback == "bedrock":
                    if config.aws_profile:
                        fallback_kwargs["profile"] = config.aws_profile
                    if config.aws_region:
                        fallback_kwargs["region"] = config.aws_region
                provider = default_provider_registry.create(fallback, **fallback_kwargs)
                break
            except (KeyError, Exception):
                continue
        else:
            raise RuntimeError(
                "No eval provider available. Install agenteval[ollama] or agenteval[openai]"
            )
    return EvalModel(provider=provider)
