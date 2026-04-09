"""Context utilization evaluator — checks if agent used retrieved context."""

from __future__ import annotations

import json

from agenteval.core.eval_model import _extract_json_object
from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator
from agenteval.providers.base import EvalProvider


class ContextUtilizationEvaluator(Evaluator):
    name = "context_utilization"

    def __init__(self, provider: EvalProvider | None = None) -> None:
        self._provider = provider

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        threshold = criteria.get("threshold", 0.6)

        context_pieces = []
        for turn in trace.turns:
            for tc in turn.tool_calls:
                if tc.result:
                    context_pieces.append(str(tc.result))

        if not context_pieces:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No retrieved context to check utilization against",
                details={},
            )

        if self._provider is None:
            return EvalResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                reason="No eval provider configured for context utilization check",
                details={},
            )

        context_text = "\n".join(f"- {c}" for c in context_pieces)
        prompt = (
            "You are a context utilization judge. Score how well the agent's response "
            "uses the retrieved context to answer the user's question.\n\n"
            f"USER INPUT: {trace.input}\n\n"
            f"RETRIEVED CONTEXT (from tools):\n{context_text}\n\n"
            f"AGENT OUTPUT: {trace.output}\n\n"
            "Scoring guide:\n"
            "- 1.0: Response directly uses key facts from the context to answer the question\n"
            "- 0.5: Response partially uses context but misses important details\n"
            "- 0.0: Response ignores the context entirely or contradicts it\n\n"
            "Paraphrasing context is fine — what matters is whether the agent incorporated "
            "the relevant information.\n\n"
            'Respond ONLY with JSON: {"utilization_score": 0.X}\nJSON:'
        )

        raw = self._provider.judge(prompt)
        score = self._parse_score(raw)
        passed = score >= threshold

        return EvalResult(
            evaluator=self.name,
            score=min(1.0, max(0.0, score)),
            passed=passed,
            reason=(
                f"Context utilization {score:.2f} meets threshold {threshold}"
                if passed
                else f"Context utilization {score:.2f} below threshold {threshold}"
            ),
            details={
                "utilization_score": score,
                "threshold": threshold,
                "context_count": len(context_pieces),
            },
        )

    def _parse_score(self, raw: str) -> float:
        try:
            json_str = _extract_json_object(raw)
            if json_str:
                data = json.loads(json_str)
                return min(1.0, max(0.0, float(data.get("utilization_score", 0.0))))
        except (json.JSONDecodeError, ValueError):
            pass
        return 0.0
