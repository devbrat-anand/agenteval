from agenteval.core.models import LLMCall
from agenteval.interceptors.base import Interceptor, InterceptorRegistry


class FakeInterceptor(Interceptor):
    name = "fake"
    package_marker = "fake_package"

    def activate(self) -> None:
        self._active = True

    def deactivate(self) -> None:
        self._active = False

    def get_calls(self) -> list[LLMCall]:
        return []

    def clear(self) -> None:
        pass


def test_interceptor_interface() -> None:
    interceptor = FakeInterceptor()
    interceptor.activate()
    assert interceptor.get_calls() == []
    interceptor.deactivate()


def test_registry_register_and_get() -> None:
    registry = InterceptorRegistry()
    registry.register(FakeInterceptor)
    assert "fake" in registry.available()


def test_registry_create_by_name() -> None:
    registry = InterceptorRegistry()
    registry.register(FakeInterceptor)
    interceptor = registry.create("fake")
    assert isinstance(interceptor, FakeInterceptor)


def test_registry_create_unknown_raises() -> None:
    registry = InterceptorRegistry()
    try:
        registry.create("nonexistent")
        raise AssertionError("Should have raised")
    except KeyError:
        pass
