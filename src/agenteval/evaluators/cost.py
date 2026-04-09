"""Cost budget evaluator."""

from __future__ import annotations

from typing import Any

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class CostEvaluator(Evaluator):
    name = "cost"

    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult:
        if "max_cost_usd" not in criteria:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No cost budget specified",
                details={},
            )

        max_cost = criteria["max_cost_usd"]
        actual_cost = trace.total_cost_usd

        if actual_cost <= max_cost:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason=f"Cost ${actual_cost:.4f} within budget ${max_cost:.4f}",
                details={"actual_cost_usd": actual_cost, "max_cost_usd": max_cost},
            )

        overage_ratio = (actual_cost - max_cost) / max_cost
        score = max(0.0, 1.0 - overage_ratio)

        return EvalResult(
            evaluator=self.name,
            score=score,
            passed=False,
            reason=f"Cost ${actual_cost:.4f} exceeds budget ${max_cost:.4f}",
            details={
                "actual_cost_usd": actual_cost,
                "max_cost_usd": max_cost,
                "overage_usd": actual_cost - max_cost,
            },
        )
