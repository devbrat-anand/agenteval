"""Tool call pattern evaluator."""

from __future__ import annotations

from typing import Any

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class ToolCallEvaluator(Evaluator):
    name = "tool_call"

    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult:
        all_tools = trace.all_tool_calls

        if not any(k in criteria for k in ["expected_tools", "expected_order", "forbidden_tools"]):
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No tool call criteria specified",
                details={},
            )

        if "forbidden_tools" in criteria:
            forbidden = criteria["forbidden_tools"]
            violations = [tool for tool in forbidden if tool in all_tools]
            if violations:
                return EvalResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    reason=f"Forbidden tools called: {', '.join(violations)}",
                    details={"forbidden_violations": violations},
                )

        if "expected_tools" in criteria:
            expected = criteria["expected_tools"]
            missing = [tool for tool in expected if tool not in all_tools]
            if missing:
                score = (len(expected) - len(missing)) / len(expected)
                return EvalResult(
                    evaluator=self.name,
                    score=score,
                    passed=False,
                    reason=f"Missing expected tools: {', '.join(missing)}",
                    details={"missing_tools": missing},
                )

        if "expected_order" in criteria:
            expected_order = criteria["expected_order"]
            if not self._check_order(all_tools, expected_order):
                return EvalResult(
                    evaluator=self.name,
                    score=0.5,
                    passed=False,
                    reason=f"Tools not called in expected order: {expected_order}",
                    details={"expected_order": expected_order, "actual_order": all_tools},
                )

        return EvalResult(
            evaluator=self.name,
            score=1.0,
            passed=True,
            reason="All tool call criteria met",
            details={},
        )

    def _check_order(self, actual_tools: list[str], expected_order: list[str]) -> bool:
        expected_idx = 0
        for tool in actual_tools:
            if expected_idx < len(expected_order) and tool == expected_order[expected_idx]:
                expected_idx += 1

        return expected_idx == len(expected_order)
