"""Regression evaluator — compares current trace against baseline."""

from __future__ import annotations

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class RegressionEvaluator(Evaluator):
    """Detects score drops, cost increases, and behavioral changes vs. baseline."""

    name = "regression"

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        baseline_trace: Trace | None = criteria.get("baseline_trace")
        baseline_score: float | None = criteria.get("baseline_score")
        current_score: float | None = criteria.get("current_score")
        threshold = criteria.get("threshold", 0.05)
        max_cost_increase = criteria.get("max_cost_increase", 3.0)

        if baseline_trace is None and baseline_score is None:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No baseline provided — skipping regression check",
                details={},
            )

        regressions: list[str] = []

        if baseline_score is not None and current_score is not None:
            drop = baseline_score - current_score
            if drop > threshold:
                regressions.append(
                    f"Score dropped {drop:.3f} (from {baseline_score:.3f} to "
                    f"{current_score:.3f}, threshold: {threshold})"
                )

        if baseline_trace is not None and baseline_trace.total_cost_usd > 0:
            cost_ratio = trace.total_cost_usd / baseline_trace.total_cost_usd
            if cost_ratio > max_cost_increase:
                regressions.append(
                    f"Cost increased {cost_ratio:.1f}x (from "
                    f"${baseline_trace.total_cost_usd:.4f} to ${trace.total_cost_usd:.4f})"
                )

        passed = len(regressions) == 0
        score = 1.0 if passed else 0.0

        return EvalResult(
            evaluator=self.name,
            score=score,
            passed=passed,
            reason="No regressions detected" if passed else "; ".join(regressions),
            details={"regressions": regressions, "threshold": threshold},
        )
