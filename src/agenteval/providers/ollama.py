"""Ollama eval provider for $0 local LLM-as-judge and embeddings."""

from __future__ import annotations

from typing import Any

from agenteval.providers.base import EvalProvider


class OllamaEvalProvider(EvalProvider):
    name = "ollama"

    def __init__(self, model: str = "llama3.2", embedding_model: str = "nomic-embed-text") -> None:
        self._model = model
        self._embedding_model = embedding_model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from ollama import Client  # type: ignore[import-not-found]

            self._client = Client()
        return self._client

    def judge(self, prompt: str) -> str:
        client = self._get_client()
        response = client.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        content: str = response["message"]["content"]
        return content

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        response = client.embeddings(
            model=self._embedding_model,
            prompt=text,
        )
        embedding: list[float] = response["embedding"]
        return embedding
