"""Eval provider interface — LLM providers used for judging and embedding."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EvalProvider(ABC):
    name: str = ""

    @abstractmethod
    def judge(self, prompt: str) -> str: ...

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


class EvalProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[EvalProvider]] = {}

    def register(self, provider_cls: type[EvalProvider]) -> None:
        self._providers[provider_cls.name] = provider_cls

    def available(self) -> list[str]:
        return list(self._providers.keys())

    def create(self, name: str, **kwargs: object) -> EvalProvider:
        if name not in self._providers:
            raise KeyError(f"Unknown provider: {name}. Available: {self.available()}")
        provider_cls = self._providers[name]
        return provider_cls(**kwargs)


default_provider_registry = EvalProviderRegistry()
