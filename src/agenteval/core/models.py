"""Core data models for agenteval."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Record of a single tool/function call made by an agent."""

    name: str
    arguments: dict[str, Any]
    result: Any
    timestamp: datetime
    duration_ms: float


class LLMCall(BaseModel):
    """Record of a single LLM API call."""

    provider: str
    model: str
    messages: list[dict[str, Any]]
    response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: datetime


class Turn(BaseModel):
    """One cycle of: input -> LLM reasoning -> tool calls -> response."""

    llm_calls: list[LLMCall] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)


class Trace(BaseModel):
    """Complete record of one agent run.

    Provides convenience properties for common queries on the trace data.
    Assertion methods (tool_called, no_loops, etc.) are added by the
    pytest_plugin.assertions module.
    """

    agent_name: str
    input: str
    output: str
    turns: list[Turn]
    total_cost_usd: float
    total_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def turn_count(self) -> int:
        """Number of turns in this trace."""
        return len(self.turns)

    @property
    def all_tool_calls(self) -> list[str]:
        """Flat list of all tool names called across all turns."""
        return [tc.name for turn in self.turns for tc in turn.tool_calls]

    @property
    def all_tool_call_objects(self) -> list[ToolCall]:
        """Flat list of all ToolCall objects across all turns."""
        return [tc for turn in self.turns for tc in turn.tool_calls]

    @property
    def all_llm_calls(self) -> list[LLMCall]:
        """Flat list of all LLM calls across all turns."""
        return [call for turn in self.turns for call in turn.llm_calls]


class EvalResult(BaseModel):
    """Result from a single evaluator."""

    evaluator: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Result from running one test (trace + all evaluator results)."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    test_name: str
    trace: Trace
    eval_results: list[EvalResult]
    overall_score: float
    passed: bool
    duration_ms: float


class SuiteResult(BaseModel):
    """Result from running a full test suite."""

    tests: list[TestResult]
    total_passed: int
    total_failed: int
    avg_score: float
    total_cost_usd: float
    total_duration_ms: float
    generated_at: datetime
