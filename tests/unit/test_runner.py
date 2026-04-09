"""Unit tests for AgentRunner and WrappedAgent."""

from agenteval.core.models import Trace
from agenteval.core.runner import AgentResult, AgentRunner


def test_agent_runner_wraps_callable() -> None:
    """Test that AgentRunner wraps a callable and returns AgentResult."""

    def fake_agent(prompt: str) -> str:
        return f"Response to: {prompt}"

    runner = AgentRunner(interceptors=[])  # no interceptors for unit test
    wrapped = runner.wrap(fake_agent)
    result = wrapped.run("hello")
    assert isinstance(result, AgentResult)
    assert result.output == "Response to: hello"
    assert isinstance(result.trace, Trace)


def test_agent_result_has_trace() -> None:
    """Test that AgentResult contains a valid trace."""

    def fake_agent(prompt: str) -> str:
        return "ok"

    runner = AgentRunner(interceptors=[])
    wrapped = runner.wrap(fake_agent)
    result = wrapped.run("test")
    assert result.trace.agent_name == "fake_agent"
    assert result.trace.input == "test"
    assert result.trace.output == "ok"
    assert result.trace.total_latency_ms >= 0


def test_agent_runner_with_custom_name() -> None:
    """Test that AgentRunner accepts a custom agent name."""

    def my_func(prompt: str) -> str:
        return "ok"

    runner = AgentRunner(interceptors=[])
    wrapped = runner.wrap(my_func, name="custom_agent")
    result = wrapped.run("test")
    assert result.trace.agent_name == "custom_agent"
