"""LLM-as-judge evaluator — uses an LLM to grade agent outputs."""

from __future__ import annotations

from agenteval.core.eval_model import EvalModel
from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator
from agenteval.providers.base import EvalProvider


class LLMJudgeEvaluator(Evaluator):
    name = "llm_judge"

    def __init__(self, provider: EvalProvider | None = None) -> None:
        self._provider = provider

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        if self._provider is None:
            return EvalResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                reason="No eval provider configured for LLM judge",
                details={},
            )

        eval_model = EvalModel(provider=self._provider)
        judge_criteria = criteria.get("criteria", {})
        threshold = criteria.get("threshold", 0.7)

        return eval_model.judge(trace, criteria=judge_criteria, threshold=threshold)
