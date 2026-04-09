"""Minimal agenteval setup — no real agent, just demonstrates the structure."""

import pytest
from agenteval.core.runner import AgentRunner


@pytest.fixture
def agent(agent_runner: AgentRunner):
    """A trivial echo agent for demonstration."""

    def echo_agent(prompt: str) -> str:
        return f"Echo: {prompt}"

    return agent_runner.wrap(echo_agent, name="echo_agent")
