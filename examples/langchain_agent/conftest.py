"""agenteval setup for a LangChain agent."""

import os

import pytest
from agenteval.core.runner import AgentRunner
from agent import create_langchain_agent


@pytest.fixture
def agent(agent_runner: AgentRunner):
    lc_agent = create_langchain_agent(
        base_url=os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        model=os.environ.get("OPENAI_MODEL", "azure_ai/gpt-5-mini"),
    )
    return agent_runner.wrap(lc_agent, name="langchain_agent")
