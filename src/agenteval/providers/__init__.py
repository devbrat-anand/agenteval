"""Eval providers for agenteval."""

from agenteval.providers.base import EvalProvider, EvalProviderRegistry, default_provider_registry
from agenteval.providers.bedrock import BedrockEvalProvider
from agenteval.providers.ollama import OllamaEvalProvider
from agenteval.providers.openai import OpenAIEvalProvider

default_provider_registry.register(OpenAIEvalProvider)
default_provider_registry.register(OllamaEvalProvider)
default_provider_registry.register(BedrockEvalProvider)

__all__ = [
    "EvalProvider",
    "EvalProviderRegistry",
    "default_provider_registry",
    "BedrockEvalProvider",
    "OpenAIEvalProvider",
    "OllamaEvalProvider",
]
