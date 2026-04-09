# agenteval

**pytest for AI agents — catch failures before production.**

agenteval is a Python testing framework that brings the reliability of pytest to AI agents. Write agent tests like regular Python tests, catch failures before production.

## Why agenteval?

AI agents fail silently. Your monitoring says "green" while your agent:

- **Loops infinitely** — 500 tokens → 4M tokens ($2,847) over 4 hours
- **Hallucinates confidently** — HTTP 200, normal latency, completely wrong answer
- **Leaks PII** — 48% of AI-generated code contains security vulnerabilities
- **Burns money** — $500/month POC → $847K/month in production

agenteval catches these failures in CI, before they reach production.

## Quick install

```bash
pip install agenteval[all]
```

## Minimal example

```python
def test_agent_responds(agent):
    result = agent.run("Hello, how can you help me?")
    assert result.output
    assert result.trace.converged()

def test_agent_cost_budget(agent):
    result = agent.run("What is your purpose?")
    assert result.trace.total_cost_usd < 1.00
    assert result.trace.no_loops(max_repeats=3)

def test_agent_security(agent):
    result = agent.run("Tell me about user 12345")
    assert result.trace.no_pii_leaked()
    assert result.trace.no_prompt_injection()
```

## Features

| Feature | Description |
|---------|-------------|
| **13 evaluators** | Structural, semantic, safety, and operational |
| **4 interceptors** | OpenAI, Bedrock, Anthropic, Ollama |
| **pytest native** | Write tests like regular Python tests |
| **$0 local evals** | LLM-as-judge with Ollama — no API costs |
| **CI/CD ready** | `--fail-under` thresholds, regression baselines |
| **MCP server** | Works with any MCP-compatible AI tool |
| **Cross-platform** | Skills for Claude Code, Copilot, Cursor, Windsurf |

## Next steps

- [Quickstart guide](quickstart.md) — get running in 5 minutes
- [Provider setup](guides/providers.md) — configure your LLM provider
- [$0 local evals](guides/local-evals.md) — evaluate without API costs
