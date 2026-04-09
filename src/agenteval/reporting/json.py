"""JSON reporter for machine-readable output."""

from __future__ import annotations

from pathlib import Path

from agenteval.core.models import SuiteResult
from agenteval.reporting.base import Reporter


class JsonReporter(Reporter):
    def render(self, suite: SuiteResult, output_path: Path | None = None) -> None:
        json_str = suite.model_dump_json(indent=2)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_str)
        else:
            print(json_str)
