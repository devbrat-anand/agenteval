"""Simple LangChain agent with a tool for testing."""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool


@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by ID."""
    return f"Order {order_id}: 2 items, shipped, arriving Thursday"


@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: 72F, sunny"


def create_langchain_agent(
    base_url: str | None = None,
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
):
    """Create a LangChain agent with tools."""
    kwargs: dict[str, object] = {"model": model, "temperature": 0}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    llm = ChatOpenAI(**kwargs)
    tools = [lookup_order, get_weather]
    agent = create_agent(
        llm,
        tools,
        system_prompt="You are a helpful assistant. Use tools when needed.",
    )

    def run(prompt_text: str) -> str:
        result = agent.invoke({"messages": [{"role": "user", "content": prompt_text}]})
        # Extract the final AI message text
        messages = result["messages"]
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                return msg.content
        return ""

    return run
