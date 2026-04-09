"""Loop detection evaluator."""

from __future__ import annotations

from typing import Any

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class LoopDetectorEvaluator(Evaluator):
    name = "loop_detector"

    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult:
        max_repeats = criteria.get("max_repeats", 3)

        all_tools = trace.all_tool_calls
        consecutive_result = self._check_consecutive_repeats(all_tools, max_repeats)
        if not consecutive_result["passed"]:
            return EvalResult(
                evaluator=self.name,
                score=consecutive_result["score"],
                passed=False,
                reason=consecutive_result["reason"],
                details=consecutive_result["details"],
            )

        turn_patterns = [tuple(tc.name for tc in turn.tool_calls) for turn in trace.turns]
        pattern_result = self._check_pattern_repeats(turn_patterns, max_repeats)
        if not pattern_result["passed"]:
            return EvalResult(
                evaluator=self.name,
                score=pattern_result["score"],
                passed=False,
                reason=pattern_result["reason"],
                details=pattern_result["details"],
            )

        return EvalResult(
            evaluator=self.name,
            score=1.0,
            passed=True,
            reason="No repetitive loops detected",
            details={},
        )

    def _check_consecutive_repeats(self, tools: list[str], max_repeats: int) -> dict[str, Any]:
        if not tools:
            return {"passed": True, "score": 1.0, "reason": "", "details": {}}

        current_tool = tools[0]
        current_count = 1
        max_consecutive = 1
        max_tool = current_tool

        for tool in tools[1:]:
            if tool == current_tool:
                current_count += 1
                if current_count > max_consecutive:
                    max_consecutive = current_count
                    max_tool = current_tool
            else:
                current_tool = tool
                current_count = 1

        if max_consecutive > max_repeats:
            score = max(0.0, 1.0 - (max_consecutive - max_repeats) / max_repeats)
            reason = (
                f"Tool '{max_tool}' repeated {max_consecutive} times "
                f"consecutively (max: {max_repeats})"
            )
            return {
                "passed": False,
                "score": score,
                "reason": reason,
                "details": {
                    "max_consecutive_repeats": max_consecutive,
                    "max_allowed": max_repeats,
                },
            }

        return {"passed": True, "score": 1.0, "reason": "", "details": {}}

    def _check_pattern_repeats(
        self, patterns: list[tuple[str, ...]], max_repeats: int
    ) -> dict[str, Any]:
        if len(patterns) <= 1:
            return {"passed": True, "score": 1.0, "reason": "", "details": {}}

        current_pattern = patterns[0]
        current_count = 1
        max_pattern_repeats = 1
        max_pattern = current_pattern

        for pattern in patterns[1:]:
            if pattern == current_pattern:
                current_count += 1
                if current_count > max_pattern_repeats:
                    max_pattern_repeats = current_count
                    max_pattern = current_pattern
            else:
                current_pattern = pattern
                current_count = 1

        if max_pattern_repeats > max_repeats:
            score = max(0.0, 1.0 - (max_pattern_repeats - max_repeats) / max_repeats)
            reason = (
                f"Turn pattern {max_pattern} repeated "
                f"{max_pattern_repeats} times (max: {max_repeats})"
            )
            return {
                "passed": False,
                "score": score,
                "reason": reason,
                "details": {
                    "max_pattern_repeats": max_pattern_repeats,
                    "max_allowed": max_repeats,
                    "pattern": list(max_pattern),
                },
            }

        return {"passed": True, "score": 1.0, "reason": "", "details": {}}
