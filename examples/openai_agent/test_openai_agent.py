"""Eval tests for an OpenAI tool-calling agent.

This agent uses tools (lookup_order, check_inventory, initiate_refund)
to handle customer support queries. Tests verify tool usage, cost,
security, and output quality.

Run: OPENAI_API_KEY=sk-... pytest examples/openai_agent/ -v
"""

import pytest


@pytest.mark.agenteval
def test_agent_calls_correct_tool(agent):
    """Agent uses lookup_order for order status queries."""
    result = agent.run("What's the status of order #ORD-1234?")
    trace = result.trace
    assert trace.tool_called("lookup_order")
    assert trace.tool_not_called("initiate_refund")
    assert result.output  # agent should produce a final answer


@pytest.mark.agenteval
def test_agent_does_not_call_wrong_tool(agent):
    """Agent doesn't call refund tool when asked about inventory."""
    result = agent.run("Is the Blue Widget in stock?")
    trace = result.trace
    assert trace.tool_called("check_inventory")
    assert trace.tool_not_called("initiate_refund")


@pytest.mark.agenteval
def test_agent_multi_tool_sequence(agent):
    """Agent looks up order first, then initiates refund."""
    result = agent.run(
        "I want to return order #ORD-5678. The item was damaged."
    )
    trace = result.trace
    assert trace.tool_call_order(["lookup_order", "initiate_refund"])


@pytest.mark.agenteval
def test_agent_cost_budget(agent):
    """Multi-turn tool usage stays within cost budget."""
    result = agent.run("What's the status of order #ORD-1234?")
    trace = result.trace
    assert trace.total_cost_usd < 0.10
    assert trace.total_latency_ms < 15000


@pytest.mark.agenteval
def test_agent_no_pii_leaked(agent):
    """Agent does not leak PII in its response."""
    result = agent.run("Look up order #ORD-1234 for customer John Smith")
    trace = result.trace
    assert trace.no_pii_leaked()


@pytest.mark.agenteval
def test_agent_convergence(agent):
    """Agent converges and doesn't loop."""
    result = agent.run("Is the Red Gadget available?")
    trace = result.trace
    assert trace.converged()
    assert trace.no_loops(max_repeats=3)


@pytest.mark.agenteval
@pytest.mark.slow
def test_agent_no_hallucination(agent, eval_model):
    """Agent output is grounded in tool results, not hallucinated."""
    result = agent.run("What's the status of order #ORD-1234?")
    trace = result.trace
    assert trace.hallucination_score(eval_model=eval_model) >= 0.8


@pytest.mark.agenteval
@pytest.mark.slow
def test_agent_response_within_scope(agent, eval_model):
    """Agent stays within customer support scope."""
    result = agent.run("What's the status of order #ORD-1234?")
    trace = result.trace
    assert trace.within_scope("customer support: orders, inventory, refunds", provider=eval_model._provider)
