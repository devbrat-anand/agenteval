"""Base reporter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agenteval.core.models import SuiteResult


class Reporter(ABC):
    @abstractmethod
    def render(self, suite: SuiteResult, output_path: Path | None = None) -> None:
        """Render a suite result."""
