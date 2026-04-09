"""Evaluator plugin interface and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agenteval.core.models import EvalResult, Trace


class Evaluator(ABC):
    name: str = ""

    @abstractmethod
    def evaluate(self, trace: Trace, criteria: dict[str, Any]) -> EvalResult: ...


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, type[Evaluator]] = {}

    def register(self, evaluator_cls: type[Evaluator]) -> None:
        self._evaluators[evaluator_cls.name] = evaluator_cls

    def available(self) -> list[str]:
        return list(self._evaluators.keys())

    def create(self, name: str) -> Evaluator:
        if name not in self._evaluators:
            raise KeyError(f"Unknown evaluator: {name}. Available: {self.available()}")
        return self._evaluators[name]()

    def discover_plugins(self) -> None:
        import sys

        if sys.version_info >= (3, 12):
            eps = entry_points(group="agenteval.evaluators")
        else:
            eps = entry_points().get("agenteval.evaluators", [])  # type: ignore[arg-type,var-annotated]
        for ep in eps:
            try:
                cls = ep.load()
                if issubclass(cls, Evaluator) and cls is not Evaluator:
                    self.register(cls)
            except Exception:
                continue


default_evaluator_registry = EvaluatorRegistry()
