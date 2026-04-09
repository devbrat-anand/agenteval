"""agenteval setup for an AWS Bedrock agent."""

import os

import pytest
from agenteval.core.runner import AgentRunner
from agent import create_bedrock_agent


@pytest.fixture
def agent(agent_runner: AgentRunner):
    bedrock_agent = create_bedrock_agent(
        profile=os.environ.get("AWS_PROFILE"),
        region=os.environ.get("AWS_REGION", "us-east-1"),
    )
    return agent_runner.wrap(bedrock_agent, name="bedrock_agent")
