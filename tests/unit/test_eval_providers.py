import pytest

from agenteval.providers.base import EvalProvider, EvalProviderRegistry
from agenteval.providers.bedrock import BedrockEvalProvider
from agenteval.providers.ollama import OllamaEvalProvider
from agenteval.providers.openai import OpenAIEvalProvider


class FakeProvider(EvalProvider):
    name = "fake"

    def judge(self, prompt: str) -> str:
        return "Score: 0.9"

    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def test_provider_interface():
    provider = FakeProvider()
    result = provider.judge("Is this helpful?")
    assert isinstance(result, str)
    embedding = provider.embed("test text")
    assert isinstance(embedding, list)
    assert len(embedding) > 0


def test_registry():
    registry = EvalProviderRegistry()
    registry.register(FakeProvider)
    assert "fake" in registry.available()
    provider = registry.create("fake")
    assert isinstance(provider, FakeProvider)


def test_registry_unknown_raises():
    registry = EvalProviderRegistry()
    with pytest.raises(KeyError):
        registry.create("nonexistent")


# --- OpenAI provider tests (unit, no real API calls) ---


def test_openai_provider_has_correct_name():
    provider = OpenAIEvalProvider(model="gpt-5-mini")
    assert provider.name == "openai"
    assert provider._model == "gpt-5-mini"


def test_openai_provider_default_model():
    provider = OpenAIEvalProvider()
    assert provider._model == "gpt-5-mini"


def test_openai_provider_base_url():
    provider = OpenAIEvalProvider(base_url="http://localhost:8080/v1")
    assert provider._base_url == "http://localhost:8080/v1"
    assert provider._api_key is None


def test_openai_provider_api_key():
    provider = OpenAIEvalProvider(api_key="sk-test-key")
    assert provider._api_key == "sk-test-key"
    assert provider._base_url is None


def test_openai_provider_base_url_and_api_key():
    provider = OpenAIEvalProvider(
        base_url="http://localhost:8080/v1",
        api_key="sk-custom",
        model="custom-model",
    )
    assert provider._base_url == "http://localhost:8080/v1"
    assert provider._api_key == "sk-custom"
    assert provider._model == "custom-model"


# --- Ollama provider tests (unit, no real API calls) ---


def test_ollama_provider_has_correct_name():
    provider = OllamaEvalProvider(model="llama3.2")
    assert provider.name == "ollama"
    assert provider._model == "llama3.2"


def test_ollama_provider_default_model():
    provider = OllamaEvalProvider()
    assert provider._model == "llama3.2"


# --- Bedrock provider tests (unit, no real API calls) ---


def test_bedrock_provider_has_correct_name():
    provider = BedrockEvalProvider(model="anthropic.claude-3-haiku-20240307-v1:0")
    assert provider.name == "bedrock"
    assert provider._model == "anthropic.claude-3-haiku-20240307-v1:0"


def test_bedrock_provider_default_models():
    provider = BedrockEvalProvider()
    assert provider._model == "anthropic.claude-3-haiku-20240307-v1:0"
    assert provider._embedding_model == "amazon.titan-embed-text-v2:0"


def test_bedrock_provider_custom_region():
    provider = BedrockEvalProvider(region="us-west-2")
    assert provider._region == "us-west-2"


def test_bedrock_provider_custom_profile():
    provider = BedrockEvalProvider(profile="my-profile")
    assert provider._profile == "my-profile"


def test_bedrock_provider_profile_and_region():
    provider = BedrockEvalProvider(profile="prod", region="eu-west-1")
    assert provider._profile == "prod"
    assert provider._region == "eu-west-1"


def test_bedrock_provider_registered():
    from agenteval.providers.base import default_provider_registry

    assert "bedrock" in default_provider_registry.available()
