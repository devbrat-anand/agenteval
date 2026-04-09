"""Simple Ollama-based agent for $0 local testing."""

from __future__ import annotations

from ollama import chat


def create_ollama_agent():
    """Create an agent using a local Ollama model."""

    def agent(prompt: str) -> str:
        response = chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Be concise."},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]

    return agent
