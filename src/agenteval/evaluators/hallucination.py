"""Hallucination evaluator — checks if output is grounded in context/tool results."""

from __future__ import annotations

import json

from agenteval.core.eval_model import _extract_json_object
from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator
from agenteval.providers.base import EvalProvider


class HallucinationEvaluator(Evaluator):
    name = "hallucination"

    def __init__(self, provider: EvalProvider | None = None) -> None:
        self._provider = provider

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        if self._provider is None:
            return EvalResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                reason="No eval provider configured for hallucination detection",
                details={},
            )

        threshold = criteria.get("threshold", 0.9)

        sources = []
        for turn in trace.turns:
            for tc in turn.tool_calls:
                sources.append(f"Tool '{tc.name}' returned: {tc.result}")

        if not sources:
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No tool results to check grounding against",
                details={"sources": []},
            )

        prompt = self._build_prompt(trace, sources)
        raw_response = self._provider.judge(prompt)
        grounding_score, ungrounded = self._parse_response(raw_response)

        passed = grounding_score >= threshold

        return EvalResult(
            evaluator=self.name,
            score=min(1.0, max(0.0, grounding_score)),
            passed=passed,
            reason=(
                f"Grounding score: {grounding_score:.2f}"
                f" — output is grounded in source data"
                if not ungrounded
                else f"Grounding score: {grounding_score:.2f}"
                f" — ungrounded claims: {'; '.join(ungrounded)}"
            ),
            details={
                "grounding_score": grounding_score,
                "ungrounded_claims": ungrounded,
                "threshold": threshold,
                "source_count": len(sources),
            },
        )

    def _build_prompt(self, trace: Trace, sources: list[str]) -> str:
        sources_text = "\n".join(f"  - {s}" for s in sources)
        return (
            "You are a hallucination detection judge. Check if the agent's output "
            "is grounded in the provided source data.\n\n"
            f"USER QUESTION: {trace.input}\n\n"
            f"AGENT OUTPUT: {trace.output}\n\n"
            f"SOURCE DATA (tool results):\n{sources_text}\n\n"
            "IMPORTANT: Paraphrasing, rewording, and reformatting source data"
            " is NOT hallucination. "
            "Only flag claims that introduce NEW information not present"
            " or implied by the source data. "
            "For example, 'shipped' and 'has been shipped' mean the same thing"
            " and are both grounded.\n\n"
            "Score the output from 0.0 (completely hallucinated) to 1.0 (fully grounded).\n"
            "List any claims that introduce genuinely new facts"
            " NOT supported by the source data.\n\n"
            "Respond ONLY with JSON: "
            '{"grounding_score": 0.X, "ungrounded_claims": ["claim1", ...]}\n'
            "JSON:"
        )

    def _parse_response(self, raw: str) -> tuple[float, list[str]]:
        try:
            json_str = _extract_json_object(raw)
            if json_str:
                data = json.loads(json_str)
                score = min(1.0, max(0.0, float(data.get("grounding_score", 0.0))))
                claims = data.get("ungrounded_claims", [])
                return score, claims if isinstance(claims, list) else []
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return 0.0, ["Failed to parse hallucination check response"]
