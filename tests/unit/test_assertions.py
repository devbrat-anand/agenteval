"""Unit tests for Trace assertion methods."""

from datetime import datetime, timezone

from agenteval.core.models import ToolCall, Trace, Turn
from agenteval.pytest_plugin.assertions import patch_trace_assertions

patch_trace_assertions()


def _make_trace(tool_names: list[str], output: str = "test output") -> Trace:
    """Helper to create a Trace with specific tool calls."""
    now = datetime.now(timezone.utc)
    tool_calls = [
        ToolCall(name=n, arguments={}, result={}, timestamp=now, duration_ms=50.0)
        for n in tool_names
    ]
    return Trace(
        agent_name="test",
        input="x",
        output=output,
        turns=[Turn(llm_calls=[], tool_calls=tool_calls)],
        total_cost_usd=0.05,
        total_latency_ms=500.0,
        total_input_tokens=100,
        total_output_tokens=50,
        metadata={},
    )


def test_tool_called_true() -> None:
    """Test tool_called returns True when tool was called."""
    assert _make_trace(["search", "book"]).tool_called("search") is True


def test_tool_called_false() -> None:
    """Test tool_called returns False when tool was not called."""
    assert _make_trace(["search"]).tool_called("book") is False


def test_tool_call_order_true() -> None:
    """Test tool_call_order returns True when order matches."""
    assert _make_trace(["search", "book", "confirm"]).tool_call_order(["search", "book"]) is True


def test_tool_call_order_false() -> None:
    """Test tool_call_order returns False when order doesn't match."""
    assert _make_trace(["book", "search"]).tool_call_order(["search", "book"]) is False


def test_tool_not_called_true() -> None:
    """Test tool_not_called returns True when tool was not called."""
    assert _make_trace(["search"]).tool_not_called("delete") is True


def test_tool_not_called_false() -> None:
    """Test tool_not_called returns False when tool was called."""
    assert _make_trace(["search", "delete"]).tool_not_called("delete") is False


def test_no_loops_true() -> None:
    """Test no_loops returns True when no loops detected."""
    assert _make_trace(["a", "b", "c"]).no_loops(max_repeats=2) is True


def test_no_loops_false() -> None:
    """Test no_loops returns False when loops detected."""
    assert _make_trace(["a", "a", "a", "a"]).no_loops(max_repeats=2) is False


def test_output_contains_true() -> None:
    """Test output_contains returns True when keyword found."""
    assert (
        _make_trace([], output="Flight AA123 booked successfully").output_contains("booked") is True
    )


def test_output_contains_false() -> None:
    """Test output_contains returns False when keyword not found."""
    assert _make_trace([], output="Error occurred").output_contains("booked") is False


def test_output_matches_true() -> None:
    """Test output_matches returns True when pattern matches."""
    assert (
        _make_trace([], output="Flight AA123 booked").output_matches(r"Flight [A-Z]{2}\d+ booked")
        is True
    )


def test_output_matches_false() -> None:
    """Test output_matches returns False when pattern doesn't match."""
    assert (
        _make_trace([], output="Something else").output_matches(r"Flight [A-Z]{2}\d+ booked")
        is False
    )
