"""AWS Bedrock tool-calling agent — a knowledge base lookup agent."""

from __future__ import annotations

import json

import boto3

TOOLS = [
    {
        "toolSpec": {
            "name": "search_knowledge_base",
            "description": "Search the company knowledge base for relevant articles.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
        },
    },
    {
        "toolSpec": {
            "name": "get_product_details",
            "description": "Get detailed information about a product by name or SKU.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "product": {"type": "string", "description": "Product name or SKU"},
                    },
                    "required": ["product"],
                },
            },
        },
    },
    {
        "toolSpec": {
            "name": "create_support_ticket",
            "description": "Create a support ticket for issues that need human follow-up.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "Ticket subject"},
                        "description": {"type": "string", "description": "Issue description"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                    "required": ["subject", "description", "priority"],
                },
            },
        },
    },
]

# Simulated tool responses
TOOL_HANDLERS = {
    "search_knowledge_base": lambda args: json.dumps({
        "results": [
            {"title": "Return Policy", "content": "Items can be returned within 30 days of purchase."},
            {"title": "Shipping FAQ", "content": "Standard shipping takes 3-5 business days."},
        ],
        "query": args["query"],
    }),
    "get_product_details": lambda args: json.dumps({
        "product": args["product"],
        "price": "$29.99",
        "category": "Electronics",
        "availability": "In Stock",
        "rating": 4.5,
    }),
    "create_support_ticket": lambda args: json.dumps({
        "ticket_id": "TKT-98765",
        "subject": args["subject"],
        "priority": args["priority"],
        "status": "open",
    }),
}


def create_bedrock_agent(profile: str | None = None, region: str = "us-east-1"):
    """Create a tool-calling Bedrock agent using the Converse API."""
    session_kwargs: dict[str, str] = {"region_name": region}
    if profile:
        session_kwargs["profile_name"] = profile
    session = boto3.Session(**session_kwargs)
    client = session.client("bedrock-runtime")
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    def agent(prompt: str) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        system = [{"text": (
            "You are a helpful product support agent. Use tools to search the "
            "knowledge base, look up products, and create tickets when needed. "
            "Always ground your answers in tool results."
        )}]

        # Agent loop: call LLM, execute tools, repeat until done
        for _ in range(5):
            response = client.converse(
                modelId=model_id,
                messages=messages,
                system=system,
                toolConfig={"tools": TOOLS},
                inferenceConfig={"maxTokens": 500},
            )

            output_message = response["output"]["message"]
            stop_reason = response["stopReason"]
            messages.append(output_message)

            if stop_reason == "end_turn":
                # Extract final text
                for block in output_message["content"]:
                    if "text" in block:
                        return block["text"]
                return ""

            if stop_reason == "tool_use":
                tool_results = []
                for block in output_message["content"]:
                    if "toolUse" in block:
                        tool = block["toolUse"]
                        handler = TOOL_HANDLERS.get(tool["name"])
                        result = handler(tool["input"]) if handler else '{"error": "unknown"}'
                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool["toolUseId"],
                                "content": [{"json": json.loads(result)}],
                            }
                        })
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                break

        return ""

    return agent
