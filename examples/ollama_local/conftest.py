"""agenteval setup for a local Ollama agent — $0 evals."""

import pytest
from agenteval.core.runner import AgentRunner
from agent import create_ollama_agent


@pytest.fixture
def agent(agent_runner: AgentRunner):
    ollama_agent = create_ollama_agent()
    return agent_runner.wrap(ollama_agent, name="ollama_agent")
