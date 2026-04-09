"""Convergence evaluator — checks if the agent reached a final answer."""

from __future__ import annotations

import re

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator

_DEFAULT_ERROR_PATTERNS = [
    r"i('m|\s+am)\s+sorry.*(?:cannot|can't|unable)",
    r"(?:error|exception)\s+occurred",
    r"i\s+(?:cannot|can't)\s+(?:complete|finish|do)",
    r"something\s+went\s+wrong",
]


class ConvergenceEvaluator(Evaluator):
    name = "convergence"

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        max_turns = criteria.get("max_turns")
        error_patterns = criteria.get("error_patterns", _DEFAULT_ERROR_PATTERNS)
        failures: list[str] = []

        if not trace.output or not trace.output.strip():
            failures.append("Agent produced empty output")

        for pattern in error_patterns:
            if re.search(pattern, trace.output, re.IGNORECASE):
                failures.append(f"Output matches error pattern: {pattern}")
                break

        if max_turns is not None and trace.turn_count > max_turns:
            failures.append(f"Agent took {trace.turn_count} turns (max: {max_turns})")

        passed = len(failures) == 0
        score = 1.0 if passed else 0.0

        return EvalResult(
            evaluator=self.name,
            score=score,
            passed=passed,
            reason="Agent converged on a final answer" if passed else "; ".join(failures),
            details={"turn_count": trace.turn_count, "failures": failures},
        )
