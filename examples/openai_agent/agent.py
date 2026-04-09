"""OpenAI tool-calling agent — a customer support agent with tools."""

from __future__ import annotations

import json

from openai import OpenAI

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up the status of a customer order by order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to look up"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check if a product is in stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Name of the product"},
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_refund",
            "description": "Initiate a refund for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to refund"},
                    "reason": {"type": "string", "description": "Reason for the refund"},
                },
                "required": ["order_id", "reason"],
            },
        },
    },
]

# Simulated tool responses (in production, these would hit real APIs)
TOOL_HANDLERS = {
    "lookup_order": lambda args: json.dumps({
        "order_id": args["order_id"],
        "status": "delivered",
        "items": ["Blue Widget x2", "Red Gadget x1"],
        "total": "$47.99",
        "delivered_at": "2025-03-15",
    }),
    "check_inventory": lambda args: json.dumps({
        "product": args["product_name"],
        "in_stock": True,
        "quantity": 42,
        "warehouse": "US-East",
    }),
    "initiate_refund": lambda args: json.dumps({
        "order_id": args["order_id"],
        "refund_status": "approved",
        "refund_amount": "$47.99",
        "reason": args["reason"],
    }),
}


def create_openai_agent(
    base_url: str | None = None,
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
):
    """Create a tool-calling OpenAI agent for customer support."""
    kwargs: dict[str, str] = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    client = OpenAI(**kwargs)

    def agent(prompt: str) -> str:
        messages = [
            {"role": "system", "content": (
                "You are a customer support agent. Use tools to look up orders, "
                "check inventory, and process refunds. Always verify information "
                "with tools before responding. Never make up order details."
            )},
            {"role": "user", "content": prompt},
        ]

        # Agent loop: call LLM, execute tools, repeat until done
        for _ in range(5):  # max 5 iterations to prevent infinite loops
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                max_tokens=500,
            )
            choice = response.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls or []:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    handler = TOOL_HANDLERS.get(fn_name)
                    result = handler(fn_args) if handler else '{"error": "unknown tool"}'
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                return choice.message.content or ""

        return messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""

    return agent
