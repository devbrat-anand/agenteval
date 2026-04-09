"""Base interceptor interface and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agenteval.core.models import LLMCall


class Interceptor(ABC):
    name: str = ""
    package_marker: str = ""

    @abstractmethod
    def activate(self) -> None: ...

    @abstractmethod
    def deactivate(self) -> None: ...

    @abstractmethod
    def get_calls(self) -> list[LLMCall]: ...

    @abstractmethod
    def clear(self) -> None: ...


class InterceptorRegistry:
    def __init__(self) -> None:
        self._interceptors: dict[str, type[Interceptor]] = {}

    def register(self, interceptor_cls: type[Interceptor]) -> None:
        self._interceptors[interceptor_cls.name] = interceptor_cls

    def available(self) -> list[str]:
        return list(self._interceptors.keys())

    def create(self, name: str) -> Interceptor:
        if name not in self._interceptors:
            raise KeyError(f"Unknown interceptor: {name}. Available: {self.available()}")
        return self._interceptors[name]()

    def auto_detect(self) -> list[Interceptor]:
        detected: list[Interceptor] = []
        for cls in self._interceptors.values():
            if cls.package_marker:
                try:
                    __import__(cls.package_marker)
                    detected.append(cls())
                except ImportError:
                    continue

        return detected


default_registry = InterceptorRegistry()
