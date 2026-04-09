"""Agent runner — wraps agent callables with interception."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from agenteval.interceptors.base import Interceptor

from agenteval.core.models import LLMCall, ToolCall, Trace, Turn
from agenteval.interceptors.base import default_registry


def _extract_tool_calls(call: LLMCall) -> list[ToolCall]:

    tool_calls: list[ToolCall] = []
    tool_results_by_id: dict[str, Any] = {}

    for msg in call.messages:
        role = msg.get("role", "")
        content = msg.get("content")

        if role == "assistant":
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                tool_calls.append(
                    ToolCall(
                        name=fn.get("name", "unknown"),
                        arguments=_safe_parse_json(fn.get("arguments", "{}")),
                        result=None,
                        timestamp=call.timestamp,
                        duration_ms=0.0,
                    )
                )

        if role == "tool":
            tool_calls.append(
                ToolCall(
                    name=msg.get("name", msg.get("tool_call_id", "unknown")),
                    arguments={},
                    result=msg.get("content", ""),
                    timestamp=call.timestamp,
                    duration_ms=0.0,
                )
            )

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "toolResult" in block:
                    tr = block["toolResult"]
                    tool_results_by_id[tr.get("toolUseId", "")] = tr.get("content", "")

    for msg in call.messages:
        content = msg.get("content")
        if msg.get("role") == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "toolUse" in block:
                    tu = block["toolUse"]
                    use_id = tu.get("toolUseId", "")
                    tool_calls.append(
                        ToolCall(
                            name=tu.get("name", "unknown"),
                            arguments=tu.get("input", {}),
                            result=tool_results_by_id.get(use_id),
                            timestamp=call.timestamp,
                            duration_ms=0.0,
                        )
                    )

    return tool_calls


def _safe_parse_json(s: str | dict) -> dict:
    if isinstance(s, dict):
        return s
    try:
        import json

        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}


@dataclass
class AgentResult:
    output: str
    trace: Trace


class WrappedAgent:
    def __init__(
        self, fn: Callable[[str], str], name: str, interceptors: list[Interceptor]
    ) -> None:
        self._fn = fn
        self._name = name
        self._interceptors = interceptors

    def run(self, prompt: str) -> AgentResult:
        for interceptor in self._interceptors:
            interceptor.clear()
            interceptor.activate()

        start = time.monotonic()
        try:
            output = self._fn(prompt)
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            for interceptor in self._interceptors:
                interceptor.deactivate()

        all_llm_calls: list[LLMCall] = []
        for interceptor in self._interceptors:
            all_llm_calls.extend(interceptor.get_calls())

        turns: list[Turn] = []
        for call in all_llm_calls:
            tool_calls = _extract_tool_calls(call)
            turns.append(Turn(llm_calls=[call], tool_calls=tool_calls))

        total_cost = sum(c.cost_usd for c in all_llm_calls)
        total_input = sum(c.input_tokens for c in all_llm_calls)
        total_output = sum(c.output_tokens for c in all_llm_calls)

        trace = Trace(
            agent_name=self._name,
            input=prompt,
            output=str(output),
            turns=turns,
            total_cost_usd=total_cost,
            total_latency_ms=elapsed_ms,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            metadata={},
        )
        result = AgentResult(output=str(output), trace=trace)

        try:
            from agenteval.pytest_plugin._collector import collect_trace

            collect_trace(trace)
        except Exception:
            pass

        return result


class AgentRunner:
    def __init__(self, interceptors: list[Interceptor] | None = None) -> None:
        if interceptors is not None:
            self._interceptors = interceptors
        else:
            self._interceptors = default_registry.auto_detect()

    def wrap(self, fn: Callable[[str], str], name: str | None = None) -> WrappedAgent:
        agent_name = name or fn.__name__
        return WrappedAgent(fn=fn, name=agent_name, interceptors=self._interceptors)
