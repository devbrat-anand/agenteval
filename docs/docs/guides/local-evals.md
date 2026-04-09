# $0 Local Evals

Run agent evaluations with **zero API cost** using Ollama for LLM-as-judge evaluations.

## Why Local Evals?

**Problem**: LLM-as-judge evaluations (semantic similarity, hallucination detection, etc.) can cost $0.01-$0.10 per test. For 1,000 tests:

| Provider | Cost per Test | 1K Tests | 10K Tests |
|----------|---------------|----------|-----------|
| GPT-4 | $0.10 | $100 | $1,000 |
| GPT-4o-mini | $0.01 | $10 | $100 |
| Claude Haiku | $0.02 | $20 | $200 |
| **Ollama** | **$0.00** | **$0** | **$0** |

**Solution**: Use Ollama to run evaluation models locally. Your agent can still use cloud APIs — only the evaluation step runs locally.

## Setup

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai
```

### 2. Install agenteval with Ollama support

```bash
pip install agenteval[ollama]
```

### 3. Pull an evaluation model

```bash
# Fast, good quality (recommended)
ollama pull llama3.2

# Alternatives
ollama pull mistral       # Fast, smaller
ollama pull llama3.1      # Larger, higher quality
ollama pull qwen2.5       # Good for reasoning
```

### 4. Start Ollama server

```bash
ollama serve
```

## Usage

### Configure eval provider

In your `conftest.py`:

```python
import pytest
from agenteval.core.eval_model import EvalModel


@pytest.fixture
def eval_model():
    """Use Ollama for $0 evaluations."""
    return EvalModel(provider="ollama", model="llama3.2")
```

That's it. Your agent tests now use Ollama for LLM-as-judge evaluations.

### Full example

```python
# conftest.py
import pytest
from agenteval.core.runner import AgentRunner
from agenteval.core.eval_model import EvalModel


@pytest.fixture
def agent(agent_runner: AgentRunner):
    """Agent uses OpenAI (cloud API)."""
    from openai import OpenAI
    client = OpenAI()
    
    def my_agent(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    
    return agent_runner.wrap(my_agent, name="my_agent")


@pytest.fixture
def eval_model():
    """Evaluations use Ollama (local, $0)."""
    return EvalModel(provider="ollama", model="llama3.2")
```

```python
# test_agent.py
import pytest


@pytest.mark.agenteval
def test_agent_no_hallucination(agent, eval_model):
    """Ollama evaluates hallucination — $0 cost."""
    result = agent.run("What is the capital of France?")
    trace = result.trace
    
    # This uses Ollama for evaluation, not OpenAI
    assert trace.hallucination_score(eval_model=eval_model) >= 0.8


@pytest.mark.agenteval
def test_semantic_similarity(agent, eval_model):
    """Ollama evaluates semantic similarity — $0 cost."""
    result = agent.run("Explain machine learning.")
    trace = result.trace
    
    expected = "ML is about computers learning from data"
    assert trace.semantic_similarity(expected, eval_model=eval_model) >= 0.7
```

## Provider Priority

agenteval auto-selects the evaluation provider. To force Ollama:

### Option 1: Environment variable (global)

```bash
export AGENTEVAL_EVAL_PROVIDER="ollama"
export AGENTEVAL_EVAL_MODEL="llama3.2"
```

### Option 2: Fixture (per-test-suite)

```python
@pytest.fixture
def eval_model():
    return EvalModel(provider="ollama", model="llama3.2")
```

### Option 3: Per-test

```python
def test_hallucination(agent):
    from agenteval.core.eval_model import EvalModel
    eval_model = EvalModel(provider="ollama", model="llama3.2")
    
    result = agent.run("...")
    assert result.trace.hallucination_score(eval_model=eval_model) >= 0.8
```

## Performance

Local models are slower than cloud APIs, but cost $0:

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `mistral` | ~2s | Good | Fast CI runs |
| `llama3.2` | ~4s | Great | Recommended default |
| `llama3.1` | ~8s | Excellent | High-accuracy evals |
| `qwen2.5` | ~5s | Great | Reasoning tasks |

**Tip**: Use `mistral` in CI for speed, `llama3.2` locally for quality.

## Hybrid Setup

Combine cloud agents with local evals:

```python
@pytest.fixture
def agent(agent_runner: AgentRunner):
    """Production agent uses GPT-4 (cloud)."""
    from openai import OpenAI
    client = OpenAI()
    
    def my_agent(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4",  # Cloud API
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    
    return agent_runner.wrap(my_agent, name="my_agent")


@pytest.fixture
def eval_model():
    """Evals use Ollama (local, $0)."""
    return EvalModel(provider="ollama", model="llama3.2")
```

This way:
- **Agent execution** uses GPT-4 (high quality, cloud cost)
- **Evaluation** uses Ollama (local, $0 cost)

Perfect for:
- Development and testing
- CI/CD pipelines
- Large-scale regression testing

## Cost Comparison

Real-world example: 500 agent tests with 3 LLM-judge evaluations each (1,500 eval calls).

| Provider | Cost |
|----------|------|
| GPT-4 | $150 |
| GPT-4o-mini | $15 |
| Claude Haiku | $30 |
| **Ollama** | **$0** |

For 10 CI runs per day over a month (15,000 eval calls):

| Provider | Monthly Cost |
|----------|--------------|
| GPT-4 | $1,500 |
| GPT-4o-mini | $150 |
| Claude Haiku | $300 |
| **Ollama** | **$0** |

## Which Evaluators Support Local Evals?

All LLM-as-judge evaluators support Ollama:

- `hallucination_score()` — Detect hallucinations
- `semantic_similarity()` — Compare semantic meaning
- `prompt_injection_detected()` — Detect prompt injection
- `pii_leaked()` — Detect PII leakage
- `output_quality()` — Score output quality

Structural evaluators (e.g., `no_loops()`, `tool_called()`, `converged()`) don't use LLMs — they're always free.

## Troubleshooting

### "Connection refused"

**Problem**: Ollama server not running.

**Solution**:
```bash
ollama serve
```

### "Model not found"

**Problem**: Model not pulled locally.

**Solution**:
```bash
ollama pull llama3.2
```

### "Out of memory"

**Problem**: Model too large for your hardware.

**Solution**: Use a smaller model:
```bash
ollama pull mistral  # Smaller, faster
```

### Slow evaluations

**Problem**: Local model inference is slow.

**Solution**:
1. Use a smaller model (`mistral` instead of `llama3.1`)
2. Enable GPU acceleration (auto-detected by Ollama)
3. Reduce batch size: `ollama serve --parallel 1`

## CI/CD Integration

Use Ollama in CI for $0 eval costs:

```yaml
# .github/workflows/agent-evals.yml
name: Agent Evals
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          ollama serve &
          sleep 5
          ollama pull llama3.2
      
      - name: Run evals
        env:
          AGENTEVAL_EVAL_PROVIDER: ollama
          AGENTEVAL_EVAL_MODEL: llama3.2
        run: |
          pip install agenteval[all]
          agenteval run tests/agent_evals/ -v
```

## Recommended Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `mistral` | 7B | Fast | Good | CI, fast iteration |
| `llama3.2` | 8B | Medium | Great | Default recommendation |
| `llama3.1` | 8B | Medium | Excellent | High-accuracy evals |
| `qwen2.5` | 7B | Medium | Great | Reasoning, complex evals |

Start with `llama3.2` — it's the best balance of speed and quality.

## Next Steps

- [Provider Setup](providers.md) — Configure other providers
- [CI/CD Integration](ci-cd.md) — Use Ollama in GitHub Actions
- [Custom Evaluators](custom-evaluators.md) — Write evaluators that use Ollama
