"""Eval tests for a LangChain tool-using agent.

Run: OPENAI_BASE_URL=https://api.openai.com OPENAI_API_KEY=sk-... pytest examples/langchain_agent/ -v
"""

import pytest


@pytest.mark.agenteval
def test_agent_uses_correct_tool(agent):
    """Agent calls lookup_order for order queries."""
    result = agent.run("What's the status of order #12345?")
    trace = result.trace
    assert trace.tool_called("lookup_order")
    assert trace.tool_not_called("get_weather")


@pytest.mark.agenteval
def test_agent_tool_order(agent):
    """Agent calls tools in the expected sequence."""
    result = agent.run("Look up order ABC then check the weather in NYC")
    trace = result.trace
    assert trace.tool_call_order(["lookup_order", "get_weather"])


@pytest.mark.agenteval
def test_agent_cost_and_convergence(agent):
    result = agent.run("What is order #99999?")
    trace = result.trace
    assert trace.total_cost_usd < 0.50
    assert trace.converged()
    assert trace.no_loops(max_repeats=3)


@pytest.mark.agenteval
@pytest.mark.slow
def test_agent_no_hallucination(agent, eval_model):
    """Agent output is grounded in tool results."""
    result = agent.run("What's the status of order #12345?")
    trace = result.trace
    assert trace.hallucination_score(eval_model=eval_model) >= 0.8


@pytest.mark.agenteval
@pytest.mark.slow
def test_agent_response_within_scope(agent, eval_model):
    """Agent stays within customer support scope."""
    result = agent.run("What's the status of order #12345?")
    trace = result.trace
    assert trace.within_scope("customer support: orders, weather lookup", provider=eval_model._provider)
