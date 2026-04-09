"""OpenAI eval provider for LLM-as-judge and embeddings."""

from __future__ import annotations

from typing import Any

from agenteval.providers.base import EvalProvider


class OpenAIEvalProvider(EvalProvider):
    name = "openai"

    def __init__(
        self,
        model: str = "gpt-5-mini",
        embedding_model: str = "text-embedding-3-small",
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._embedding_model = embedding_model
        self._base_url = base_url
        self._api_key = api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import OpenAI  # type: ignore[import-not-found]

            kwargs: dict[str, str] = {}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = OpenAI(**kwargs)  # type: ignore[arg-type]
        return self._client

    def judge(self, prompt: str) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content: str = response.choices[0].message.content or ""
        return content

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        response = client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        embedding: list[float] = response.data[0].embedding
        return embedding
