"""AWS Bedrock eval provider for LLM-as-judge and embeddings."""

from __future__ import annotations

import json
from typing import Any

from agenteval.providers.base import EvalProvider


class BedrockEvalProvider(EvalProvider):
    name = "bedrock"

    def __init__(
        self,
        model: str = "anthropic.claude-3-haiku-20240307-v1:0",
        embedding_model: str = "amazon.titan-embed-text-v2:0",
        region: str | None = None,
        profile: str | None = None,
    ) -> None:
        self._model = model
        self._embedding_model = embedding_model
        self._region = region
        self._profile = profile
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3  # type: ignore[import-not-found]

            session_kwargs: dict[str, str] = {}
            if self._profile:
                session_kwargs["profile_name"] = self._profile
            if self._region:
                session_kwargs["region_name"] = self._region
            session = boto3.Session(**session_kwargs)
            self._client = session.client("bedrock-runtime")
        return self._client

    def judge(self, prompt: str) -> str:
        client = self._get_client()

        if self._model.startswith("anthropic."):
            return self._judge_claude(client, prompt)
        elif self._model.startswith("amazon."):
            return self._judge_titan(client, prompt)
        elif self._model.startswith("meta."):
            return self._judge_llama(client, prompt)
        else:
            return self._judge_converse(client, prompt)

    def _judge_claude(self, client: Any, prompt: str) -> str:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = client.invoke_model(modelId=self._model, body=body)
        result = json.loads(response["body"].read())
        content = result.get("content", [{}])
        return content[0].get("text", "") if content else ""

    def _judge_titan(self, client: Any, prompt: str) -> str:
        body = json.dumps(
            {
                "inputText": prompt,
                "textGenerationConfig": {"maxTokenCount": 1024, "temperature": 0.0},
            }
        )
        response = client.invoke_model(modelId=self._model, body=body)
        result = json.loads(response["body"].read())
        results = result.get("results", [{}])
        return results[0].get("outputText", "") if results else ""

    def _judge_llama(self, client: Any, prompt: str) -> str:
        body = json.dumps(
            {
                "prompt": prompt,
                "max_gen_len": 1024,
                "temperature": 0.0,
            }
        )
        response = client.invoke_model(modelId=self._model, body=body)
        result = json.loads(response["body"].read())
        return result.get("generation", "")

    def _judge_converse(self, client: Any, prompt: str) -> str:
        response = client.converse(
            modelId=self._model,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.0},
        )
        output = response.get("output", {}).get("message", {})
        content = output.get("content", [{}])
        return content[0].get("text", "") if content else ""

    def embed(self, text: str) -> list[float]:
        client = self._get_client()

        if self._embedding_model.startswith("amazon.titan-embed"):
            body = json.dumps({"inputText": text})
        elif self._embedding_model.startswith("cohere."):
            body = json.dumps({"texts": [text], "input_type": "search_document"})
        else:
            body = json.dumps({"inputText": text})

        response = client.invoke_model(modelId=self._embedding_model, body=body)
        result = json.loads(response["body"].read())

        if "embedding" in result:
            return result["embedding"]
        if "embeddings" in result:
            return result["embeddings"][0]
        return []
