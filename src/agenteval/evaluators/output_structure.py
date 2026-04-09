"""Output structure evaluator."""

from __future__ import annotations

import json
import re
from typing import Any

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class OutputStructureEvaluator(Evaluator):
    name = "output_structure"

    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult:
        output = trace.output

        if not any(k in criteria for k in ["contains", "excludes", "regex", "json_schema"]):
            return EvalResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                reason="No output structure criteria specified",
                details={},
            )

        if "excludes" in criteria:
            excludes = criteria["excludes"]
            violations = [keyword for keyword in excludes if keyword.lower() in output.lower()]
            if violations:
                return EvalResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    reason=f"Output contains forbidden keywords: {', '.join(violations)}",
                    details={"forbidden_keywords_found": violations},
                )

        if "contains" in criteria:
            required = criteria["contains"]
            missing = [keyword for keyword in required if keyword.lower() not in output.lower()]
            if missing:
                score = (len(required) - len(missing)) / len(required)
                return EvalResult(
                    evaluator=self.name,
                    score=score,
                    passed=False,
                    reason=f"Output missing required keywords: {', '.join(missing)}",
                    details={"missing_keywords": missing},
                )

        if "regex" in criteria:
            pattern = criteria["regex"]
            if not re.search(pattern, output):
                return EvalResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    reason=f"Output does not match regex pattern: {pattern}",
                    details={"pattern": pattern},
                )

        if "json_schema" in criteria:
            schema = criteria["json_schema"]
            result = self._validate_json_schema(output, schema)
            if not result["passed"]:
                return EvalResult(
                    evaluator=self.name,
                    score=0.0,
                    passed=False,
                    reason=result["reason"],
                    details=result["details"],
                )

        return EvalResult(
            evaluator=self.name,
            score=1.0,
            passed=True,
            reason="Output structure meets all criteria",
            details={},
        )

    def _validate_json_schema(self, output: str, schema: dict[str, Any]) -> dict[str, Any]:
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            return {
                "passed": False,
                "reason": f"Output is not valid JSON: {e}",
                "details": {"error": str(e)},
            }

        if "type" in schema:
            expected_type = schema["type"]
            actual_type = type(data).__name__
            type_map = {
                "object": "dict",
                "array": "list",
                "string": "str",
                "number": ("int", "float"),
                "integer": "int",
                "boolean": "bool",
                "null": "NoneType",
            }

            expected_python_type = type_map.get(expected_type, expected_type)
            if isinstance(expected_python_type, tuple):
                if actual_type not in expected_python_type:
                    reason = f"JSON type mismatch: expected {expected_type}, got {actual_type}"
                    return {
                        "passed": False,
                        "reason": reason,
                        "details": {
                            "expected_type": expected_type,
                            "actual_type": actual_type,
                        },
                    }
            elif actual_type != expected_python_type:
                reason = f"JSON type mismatch: expected {expected_type}, got {actual_type}"
                return {
                    "passed": False,
                    "reason": reason,
                    "details": {
                        "expected_type": expected_type,
                        "actual_type": actual_type,
                    },
                }

        if "required" in schema and isinstance(data, dict):
            missing_fields = [field for field in schema["required"] if field not in data]
            if missing_fields:
                return {
                    "passed": False,
                    "reason": f"JSON missing required fields: {', '.join(missing_fields)}",
                    "details": {"missing_fields": missing_fields},
                }

        return {"passed": True, "reason": "", "details": {}}
