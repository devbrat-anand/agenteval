"""EvalModel — facade for LLM-as-judge and embedding operations."""

from __future__ import annotations

import json

from agenteval.core.models import EvalResult, Trace
from agenteval.providers.base import EvalProvider


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


class EvalModel:
    def __init__(self, provider: EvalProvider) -> None:
        self._provider = provider

    def judge(
        self,
        trace: Trace,
        criteria: dict[str, str],
        threshold: float = 0.7,
    ) -> EvalResult:
        prompt = self._build_judge_prompt(trace, criteria)
        raw_response = self._provider.judge(prompt)
        scores = self._parse_scores(raw_response, list(criteria.keys()))

        all_pass = all(s >= threshold for s in scores.values())
        avg_score = sum(scores.values()) / len(scores) if scores else 0.0

        failed_criteria = [k for k, v in scores.items() if v < threshold]
        if all_pass:
            reason = "All criteria met threshold"
        else:
            reason = f"Criteria below threshold ({threshold}): {', '.join(failed_criteria)}"

        return EvalResult(
            evaluator="llm_judge",
            score=min(1.0, max(0.0, avg_score)),
            passed=all_pass,
            reason=reason,
            details={"scores": scores, "threshold": threshold, "raw_response": raw_response},
        )

    def embed(self, text: str) -> list[float]:
        return self._provider.embed(text)

    def _build_judge_prompt(self, trace: Trace, criteria: dict[str, str]) -> str:
        criteria_text = "\n".join(
            f"- {name}: {description}" for name, description in criteria.items()
        )
        return (
            "You are an AI evaluation judge. Score the following agent response "
            "on each criterion from 0.0 to 1.0.\n\n"
            f"USER INPUT: {trace.input}\n\n"
            f"AGENT OUTPUT: {trace.output}\n\n"
            f"CRITERIA:\n{criteria_text}\n\n"
            "Respond ONLY with a JSON object mapping each criterion name to a "
            "float score between 0.0 and 1.0. Example: "
            '{"helpful": 0.9, "accurate": 0.8}\n'
            "JSON:"
        )

    def _parse_scores(self, raw: str, criteria_names: list[str]) -> dict[str, float]:
        try:
            json_str = _extract_json_object(raw)
            if json_str:
                scores = json.loads(json_str)
                result: dict[str, float] = {}
                for name in criteria_names:
                    value = scores.get(name, 0.0)
                    result[name] = min(1.0, max(0.0, float(value)))
                return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return {name: 0.0 for name in criteria_names}
