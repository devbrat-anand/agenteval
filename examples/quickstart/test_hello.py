"""Quickstart example — the smallest possible agenteval test."""


def test_agent_responds(agent):
    """Agent returns a non-empty response."""
    result = agent.run("Hello, world!")
    assert result.output
    assert "Echo" in result.output


def test_agent_is_fast_and_cheap(agent):
    """Agent stays within cost and latency budgets."""
    result = agent.run("What is 2 + 2?")
    trace = result.trace
    assert trace.total_cost_usd < 1.00
    assert trace.total_latency_ms < 30000


def test_agent_no_loops(agent):
    """Agent does not enter infinite loops."""
    result = agent.run("Repeat after me: hello")
    trace = result.trace
    assert trace.no_loops(max_repeats=3)
