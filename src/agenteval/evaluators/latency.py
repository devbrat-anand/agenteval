"""Latency limit evaluator."""

from __future__ import annotations

from typing import Any

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class LatencyEvaluator(Evaluator):
    name = "latency"

    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult:
        if "max_latency_ms" not in criteria:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No latency limit specified",
                details={},
            )

        max_latency = criteria["max_latency_ms"]
        actual_latency = trace.total_latency_ms

        if actual_latency <= max_latency:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason=f"Latency {actual_latency:.0f}ms within limit {max_latency:.0f}ms",
                details={
                    "actual_latency_ms": actual_latency,
                    "max_latency_ms": max_latency,
                },
            )

        overage_ratio = (actual_latency - max_latency) / max_latency
        score = max(0.0, 1.0 - overage_ratio)

        return EvalResult(
            evaluator=self.name,
            score=score,
            passed=False,
            reason=f"Latency {actual_latency:.0f}ms exceeds limit {max_latency:.0f}ms",
            details={
                "actual_latency_ms": actual_latency,
                "max_latency_ms": max_latency,
                "overage_ms": actual_latency - max_latency,
            },
        )
