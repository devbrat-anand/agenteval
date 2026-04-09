"""Embedding similarity evaluator — compares output to golden references."""

from __future__ import annotations

import math

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator
from agenteval.providers.base import EvalProvider


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SimilarityEvaluator(Evaluator):
    name = "similarity"

    def __init__(self, provider: EvalProvider | None = None) -> None:
        self._provider = provider

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        reference = criteria.get("reference")
        threshold = criteria.get("threshold", 0.8)

        if reference is None:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No reference provided — skipping similarity check",
                details={},
            )

        if self._provider is None:
            return EvalResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                reason="No eval provider configured for embedding similarity",
                details={},
            )

        output_embedding = self._provider.embed(trace.output)
        reference_embedding = self._provider.embed(reference)
        score = _cosine_similarity(output_embedding, reference_embedding)
        passed = score >= threshold

        return EvalResult(
            evaluator=self.name,
            score=min(1.0, max(0.0, score)),
            passed=passed,
            reason=(
                f"Similarity {score:.3f} meets threshold {threshold}"
                if passed
                else f"Similarity {score:.3f} below threshold {threshold}"
            ),
            details={
                "similarity": score,
                "threshold": threshold,
            },
        )
