"""OpenAI-compatible API interceptor using httpx transport hooks."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from agenteval.core.models import LLMCall
from agenteval.interceptors.base import Interceptor
from agenteval.interceptors.pricing import PricingEngine


class OpenAIInterceptor(Interceptor):
    name = "openai"
    package_marker = "openai"

    def __init__(self) -> None:
        self._calls: list[LLMCall] = []
        self._active: bool = False
        self._pricing = PricingEngine()
        self._original_send: Any = None
        self._original_async_send: Any = None

    def activate(self) -> None:
        import httpx

        self._active = True
        self._original_send = httpx.Client.send
        self._original_async_send = httpx.AsyncClient.send
        interceptor = self
        original_send = self._original_send
        original_async_send = self._original_async_send

        def patched_send(client_self: httpx.Client, request: httpx.Request, **kwargs: Any) -> Any:
            start = time.monotonic()
            response = original_send(client_self, request, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            if interceptor._active:
                interceptor._try_capture(request, response, elapsed_ms)
            return response

        async def patched_async_send(
            client_self: httpx.AsyncClient, request: httpx.Request, **kwargs: Any
        ) -> Any:
            start = time.monotonic()
            response = await original_async_send(client_self, request, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            if interceptor._active:
                interceptor._try_capture(request, response, elapsed_ms)
            return response

        httpx.Client.send = patched_send  # type: ignore[method-assign,assignment]
        httpx.AsyncClient.send = patched_async_send  # type: ignore[method-assign,assignment]

    def deactivate(self) -> None:
        import httpx

        if self._original_send is not None:
            httpx.Client.send = self._original_send  # type: ignore[method-assign]
            self._original_send = None
        if self._original_async_send is not None:
            httpx.AsyncClient.send = self._original_async_send  # type: ignore[method-assign]
            self._original_async_send = None
        self._active = False

    def get_calls(self) -> list[LLMCall]:
        return list(self._calls)

    def clear(self) -> None:
        self._calls.clear()

    def _try_capture(self, request: Any, response: Any, latency_ms: float) -> None:
        try:
            if b"/chat/completions" not in request.url.raw_path:
                return
            import json

            request_body = json.loads(request.content)
            response_body = json.loads(response.content)
            model = response_body.get("model", request_body.get("model", "unknown"))
            messages = request_body.get("messages", [])
            choices = response_body.get("choices", [])
            response_content = ""
            if choices:
                response_content = choices[0].get("message", {}).get("content", "")
            usage = response_body.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            self._record_call(
                model=model,
                messages=messages,
                response_content=response_content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
        except Exception:
            pass

    def _record_call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        response_content: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
    ) -> None:
        cost = self._pricing.compute_cost(
            provider="openai",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        call = LLMCall(
            provider="openai",
            model=model,
            messages=messages,
            response=response_content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            timestamp=datetime.now(timezone.utc),
        )
        self._calls.append(call)
