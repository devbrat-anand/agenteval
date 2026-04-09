"""AWS Bedrock interceptor using botocore event hooks."""

from __future__ import annotations

import io
import json
import time
from datetime import datetime, timezone
from typing import Any

from agenteval.core.models import LLMCall
from agenteval.interceptors.base import Interceptor
from agenteval.interceptors.pricing import PricingEngine


class BedrockInterceptor(Interceptor):
    name = "bedrock"
    package_marker = "boto3"

    def __init__(self) -> None:
        self._calls: list[LLMCall] = []
        self._active: bool = False
        self._pricing = PricingEngine()
        self._original_make_api_call: Any = None

    def activate(self) -> None:
        self._active = True
        try:
            import botocore.client

            self._original_make_api_call = botocore.client.BaseClient._make_api_call

            interceptor = self
            original = self._original_make_api_call

            def patched_make_api_call(
                client_self: Any, operation_name: str, api_params: Any = None, **kwargs: Any
            ) -> Any:
                if not interceptor._active:
                    return original(client_self, operation_name, api_params, **kwargs)

                service_name = getattr(client_self, "_service_model", None)
                if service_name and getattr(service_name, "service_name", "") == "bedrock-runtime":
                    start = time.monotonic()
                    response = original(client_self, operation_name, api_params, **kwargs)
                    elapsed_ms = (time.monotonic() - start) * 1000
                    interceptor._try_capture(operation_name, api_params or {}, response, elapsed_ms)
                    return response

                return original(client_self, operation_name, api_params, **kwargs)

            botocore.client.BaseClient._make_api_call = patched_make_api_call
        except ImportError:
            pass

    def deactivate(self) -> None:
        if self._original_make_api_call is not None:
            try:
                import botocore.client

                botocore.client.BaseClient._make_api_call = self._original_make_api_call
            except ImportError:
                pass
            self._original_make_api_call = None
        self._active = False

    def get_calls(self) -> list[LLMCall]:
        return list(self._calls)

    def clear(self) -> None:
        self._calls.clear()

    def _try_capture(
        self, operation: str, request: dict, response: dict, latency_ms: float
    ) -> None:
        try:
            model = request.get("modelId", "unknown")

            if operation in ("InvokeModel", "InvokeModelWithResponseStream"):
                body = json.loads(request.get("body", "{}"))
                messages = body.get(
                    "messages", [{"role": "user", "content": str(body.get("prompt", ""))}]
                )
                raw_body = response.get("body")
                if raw_body is not None and hasattr(raw_body, "read"):
                    raw_bytes = raw_body.read()  # type: ignore[union-attr]
                    response["body"] = io.BytesIO(raw_bytes)
                    resp_body = json.loads(raw_bytes)
                else:
                    resp_body = json.loads(raw_body or "{}")
                content = resp_body.get("content", [{}])
                response_text = content[0].get("text", "") if content else ""
                usage = resp_body.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
            elif operation == "Converse":
                messages = request.get("messages", [])
                output_msg = response.get("output", {}).get("message", {})
                content = output_msg.get("content", [{}])
                response_text = content[0].get("text", "") if content else ""
                usage = response.get("usage", {})
                input_tokens = usage.get("inputTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
            else:
                return

            self._record_call(
                model=model,
                messages=messages,
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
        cost = self._pricing.compute_cost("bedrock", model, input_tokens, output_tokens)
        self._calls.append(
            LLMCall(
                provider="bedrock",
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
