"""Provider interceptors for agenteval."""

from agenteval.interceptors.anthropic import AnthropicInterceptor
from agenteval.interceptors.base import Interceptor, InterceptorRegistry, default_registry
from agenteval.interceptors.bedrock import BedrockInterceptor
from agenteval.interceptors.openai import OpenAIInterceptor

# Register built-in interceptors
default_registry.register(OpenAIInterceptor)
default_registry.register(BedrockInterceptor)
default_registry.register(AnthropicInterceptor)

__all__ = [
    "Interceptor",
    "InterceptorRegistry",
    "default_registry",
    "OpenAIInterceptor",
    "BedrockInterceptor",
    "AnthropicInterceptor",
]
