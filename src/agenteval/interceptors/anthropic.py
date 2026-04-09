"""Anthropic SDK interceptor."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from agenteval.core.models import LLMCall
from agenteval.interceptors.base import Interceptor
from agenteval.interceptors.pricing import PricingEngine


class AnthropicInterceptor(Interceptor):
    name = "anthropic"
    package_marker = "anthropic"

    def __init__(self) -> None:
        self._calls: list[LLMCall] = []
        self._active: bool = False
        self._pricing = PricingEngine()
        self._original_create: Any = None
        self._original_async_create: Any = None

    def activate(self) -> None:
        self._active = True
        try:
            import anthropic

            self._original_create = anthropic.resources.messages.Messages.create
            interceptor = self
            original = self._original_create

            def patched_create(self_inner: Any, *args: Any, **kwargs: Any) -> Any:
                start = time.monotonic()
                response = original(self_inner, *args, **kwargs)
                elapsed = (time.monotonic() - start) * 1000
                if interceptor._active:
                    interceptor._try_capture_messages(kwargs, response, elapsed)
                return response

            anthropic.resources.messages.Messages.create = patched_create  # type: ignore[method-assign,assignment]

            # Patch async client too
            try:
                self._original_async_create = anthropic.resources.messages.AsyncMessages.create
                original_async = self._original_async_create

                async def patched_async_create(self_inner: Any, *args: Any, **kwargs: Any) -> Any:
                    start = time.monotonic()
                    response = await original_async(self_inner, *args, **kwargs)
                    elapsed = (time.monotonic() - start) * 1000
                    if interceptor._active:
                        interceptor._try_capture_messages(kwargs, response, elapsed)
                    return response

                anthropic.resources.messages.AsyncMessages.create = patched_async_create  # type: ignore[method-assign,assignment]
            except AttributeError:
                pass
        except (ImportError, AttributeError):
            pass

    def deactivate(self) -> None:
        try:
            import anthropic

            if self._original_create is not None:
                anthropic.resources.messages.Messages.create = self._original_create  # type: ignore[method-assign]
            if self._original_async_create is not None:
                anthropic.resources.messages.AsyncMessages.create = self._original_async_create  # type: ignore[method-assign]
        except (ImportError, AttributeError):
            pass
        self._original_create = None
        self._original_async_create = None
        self._active = False

    def get_calls(self) -> list[LLMCall]:
        return list(self._calls)

    def clear(self) -> None:
        self._calls.clear()

    def _try_capture_messages(self, request: dict, response: Any, latency_ms: float) -> None:
        try:
            model = getattr(response, "model", request.get("model", "unknown"))
            messages = request.get("messages", [])
            content = getattr(response, "content", [])

            text_parts: list[str] = []
            response_messages = list(messages)
            assistant_content: list[dict[str, Any]] = []
            for block in content:
                block_type = getattr(block, "type", None)
                if block_type == "text":
                    text_parts.append(getattr(block, "text", ""))
                    assistant_content.append({"type": "text", "text": getattr(block, "text", "")})
                elif block_type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "toolUse": {
                                "toolUseId": getattr(block, "id", ""),
                                "name": getattr(block, "name", "unknown"),
                                "input": getattr(block, "input", {}),
                            },
                        }
                    )

            if assistant_content:
                response_messages.append({"role": "assistant", "content": assistant_content})

            response_text = "\n".join(text_parts)

            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

            self._record_call(
                model=model,
                messages=response_messages,
                response_content=response_text,
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
        cost = self._pricing.compute_cost("anthropic", model, input_tokens, output_tokens)
        self._calls.append(
            LLMCall(
                provider="anthropic",
                model=model,
                messages=messages,
                response=response_content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc),
            )
        )
