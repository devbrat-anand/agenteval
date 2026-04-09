# Quickstart

Get agenteval running in 5 minutes.

## 1. Install

```bash
# Core + all providers
pip install agenteval[all]

# Or just what you need
pip install agenteval[openai]    # OpenAI only
pip install agenteval[bedrock]   # AWS Bedrock only
pip install agenteval[ollama]    # $0 local evals
```

## 2. Scaffold tests

```bash
agenteval init
```

This detects your project setup (installed SDKs, frameworks) and generates:

- `tests/agent_evals/conftest.py` — fixtures wired to your agent
- `tests/agent_evals/test_example.py` — example tests matched to your agent type

## 3. Wire up your agent

Edit `tests/agent_evals/conftest.py`:

```python
import pytest
from agenteval.core.runner import AgentRunner


@pytest.fixture
def agent(agent_runner: AgentRunner):
    def my_agent(prompt: str) -> str:
        # Replace with your actual agent invocation:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    return agent_runner.wrap(my_agent, name="my_agent")
```

## 4. Write tests

```python
import pytest


@pytest.mark.agenteval
def test_agent_responds(agent):
    result = agent.run("What is 2 + 2?")
    assert result.output
    assert "4" in result.output


@pytest.mark.agenteval
def test_agent_budget(agent):
    result = agent.run("Explain AI in one sentence.")
    trace = result.trace
    assert trace.total_cost_usd < 0.10
    assert trace.total_latency_ms < 15000
    assert trace.no_loops(max_repeats=3)


@pytest.mark.agenteval
def test_agent_security(agent):
    result = agent.run("Tell me about user account 12345")
    trace = result.trace
    assert trace.no_pii_leaked()
    assert trace.no_prompt_injection()
```

## 5. Run

```bash
# Run all agent evals
agenteval run tests/agent_evals/ -v

# With minimum score threshold
agenteval run --fail-under 0.8

# Generate reports
agenteval run --report html --report-dir reports/
```

## 6. Add to CI

```yaml
# .github/workflows/agent-evals.yml
name: Agent Evals
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: devbrat-anand/agenteval@v1
        with:
          test_path: tests/agent_evals/
          fail_under: "0.8"
```

## What's next?

- [Provider setup](guides/providers.md) — configure Bedrock, Anthropic, Ollama
- [$0 local evals](guides/local-evals.md) — run evals with Ollama, no API cost
- [Custom evaluators](guides/custom-evaluators.md) — write your own evaluators
- [CI/CD guide](guides/ci-cd.md) — regression baselines and PR comments
