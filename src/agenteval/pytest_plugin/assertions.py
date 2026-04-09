"""Convenience assertion methods patched onto Trace objects."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from agenteval.evaluators.loop_detector import LoopDetectorEvaluator

if TYPE_CHECKING:
    from agenteval.core.models import EvalResult, Trace

_patched = False


def _collect(result: EvalResult) -> None:
    try:
        from agenteval.pytest_plugin._collector import collect_eval_result

        collect_eval_result(result)
    except Exception:
        pass


def _tool_called(self: Trace, tool_name: str) -> bool:
    from agenteval.core.models import EvalResult

    passed = tool_name in self.all_tool_calls
    _collect(
        EvalResult(
            evaluator="tool_called",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"{'Found' if passed else 'Missing'}: {tool_name}",
            details={"tool_name": tool_name, "actual_tools": self.all_tool_calls},
        )
    )
    return passed


def _tool_call_order(self: Trace, expected_order: list[str]) -> bool:
    from agenteval.core.models import EvalResult

    idx = 0
    for tool in self.all_tool_calls:
        if idx < len(expected_order) and tool == expected_order[idx]:
            idx += 1
    passed = idx == len(expected_order)
    _collect(
        EvalResult(
            evaluator="tool_call_order",
            score=1.0 if passed else idx / max(len(expected_order), 1),
            passed=passed,
            reason=f"Order {'matched' if passed else 'mismatch'}: expected {expected_order}",
            details={"expected": expected_order, "actual": self.all_tool_calls},
        )
    )
    return passed


def _tool_not_called(self: Trace, tool_name: str) -> bool:
    from agenteval.core.models import EvalResult

    passed = tool_name not in self.all_tool_calls
    _collect(
        EvalResult(
            evaluator="tool_not_called",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"{tool_name} {'absent' if passed else 'was called unexpectedly'}",
            details={"tool_name": tool_name, "actual_tools": self.all_tool_calls},
        )
    )
    return passed


def _no_loops(self: Trace, max_repeats: int = 3) -> bool:
    evaluator = LoopDetectorEvaluator()
    result = evaluator.evaluate(self, {"max_repeats": max_repeats})
    _collect(result)
    return result.passed


def _output_contains(self: Trace, keyword: str) -> bool:
    from agenteval.core.models import EvalResult

    passed = keyword.lower() in self.output.lower()
    _collect(
        EvalResult(
            evaluator="output_contains",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"Keyword '{keyword}' {'found' if passed else 'not found'} in output",
        )
    )
    return passed


def _output_matches(self: Trace, pattern: str) -> bool:
    from agenteval.core.models import EvalResult

    passed = bool(re.search(pattern, self.output))
    _collect(
        EvalResult(
            evaluator="output_matches",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"Pattern '{pattern}' {'matched' if passed else 'no match'}",
        )
    )
    return passed


def _hallucination_score(self: Trace, eval_model: Any = None, threshold: float = 0.0) -> float:
    from agenteval.evaluators.hallucination import HallucinationEvaluator

    provider = getattr(eval_model, "_provider", None) if eval_model else None
    evaluator = HallucinationEvaluator(provider=provider)
    result = evaluator.evaluate(self, {"threshold": threshold})
    _collect(result)
    return result.score


def _similarity_to(
    self: Trace, reference: str, threshold: float = 0.8, provider: Any = None
) -> float:
    from agenteval.evaluators.similarity import SimilarityEvaluator

    evaluator = SimilarityEvaluator(provider=provider)
    result = evaluator.evaluate(self, {"reference": reference, "threshold": threshold})
    _collect(result)
    return result.score


def _no_pii_leaked(self: Trace) -> bool:
    from agenteval.evaluators.security import SecurityEvaluator

    evaluator = SecurityEvaluator()
    result = evaluator.evaluate(
        self, {"check_pii": True, "check_credentials": False, "check_injection": False}
    )
    _collect(result)
    return result.passed


def _no_prompt_injection(self: Trace) -> bool:
    from agenteval.evaluators.security import SecurityEvaluator

    evaluator = SecurityEvaluator()
    result = evaluator.evaluate(
        self, {"check_pii": False, "check_credentials": False, "check_injection": True}
    )
    _collect(result)
    return result.passed


def _within_scope(self: Trace, scope: str, provider: Any = None) -> bool:
    from agenteval.evaluators.guardrail import GuardrailEvaluator

    evaluator = GuardrailEvaluator(provider=provider)
    result = evaluator.evaluate(self, {"scope": scope})
    _collect(result)
    return result.passed


def _converged(self: Trace) -> bool:
    from agenteval.evaluators.convergence import ConvergenceEvaluator

    result = ConvergenceEvaluator().evaluate(self, {})
    _collect(result)
    return result.passed


def _context_utilized(self: Trace, threshold: float = 0.6, provider: Any = None) -> bool:
    from agenteval.evaluators.context_utilization import ContextUtilizationEvaluator

    result = ContextUtilizationEvaluator(provider=provider).evaluate(self, {"threshold": threshold})
    _collect(result)
    return result.passed


def patch_trace_assertions() -> None:
    global _patched
    if _patched:
        return

    from agenteval.core.models import Trace

    Trace.tool_called = _tool_called  # type: ignore[attr-defined]
    Trace.tool_call_order = _tool_call_order  # type: ignore[attr-defined]
    Trace.tool_not_called = _tool_not_called  # type: ignore[attr-defined]
    Trace.no_loops = _no_loops  # type: ignore[attr-defined]
    Trace.output_contains = _output_contains  # type: ignore[attr-defined]
    Trace.output_matches = _output_matches  # type: ignore[attr-defined]
    Trace.hallucination_score = _hallucination_score  # type: ignore[attr-defined]
    Trace.similarity_to = _similarity_to  # type: ignore[attr-defined]
    Trace.no_pii_leaked = _no_pii_leaked  # type: ignore[attr-defined]
    Trace.no_prompt_injection = _no_prompt_injection  # type: ignore[attr-defined]
    Trace.within_scope = _within_scope  # type: ignore[attr-defined]
    Trace.converged = _converged  # type: ignore[attr-defined]
    Trace.context_utilized = _context_utilized  # type: ignore[attr-defined]

    _patched = True
