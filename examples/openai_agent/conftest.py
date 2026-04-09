"""agenteval setup for an OpenAI-based agent."""

import os

import pytest
from agenteval.core.runner import AgentRunner
from agent import create_openai_agent


@pytest.fixture
def agent(agent_runner: AgentRunner):
    openai_agent = create_openai_agent(
        base_url=os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    )
    return agent_runner.wrap(openai_agent, name="openai_agent")
