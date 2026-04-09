# Provider Setup

agenteval supports multiple LLM providers for both agent execution and LLM-as-judge evaluations.

## Supported Providers

| Provider | Install | Cost | Use Case |
|----------|---------|------|----------|
| OpenAI | `pip install agenteval[openai]` | $$ | GPT-4, GPT-3.5 agents |
| AWS Bedrock | `pip install agenteval[bedrock]` | $$ | Claude, Llama on AWS |
| Anthropic | `pip install agenteval[anthropic]` | $$ | Direct Claude API |
| Ollama | `pip install agenteval[ollama]` | $0 | Local models |

## OpenAI

### Installation

```bash
pip install agenteval[openai]
```

### Configuration

```bash
export OPENAI_API_KEY="sk-..."
```

### Example

```python
from openai import OpenAI

def create_agent():
    client = OpenAI()
    
    def agent(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    
    return agent
```

agenteval automatically detects and intercepts OpenAI SDK calls. No additional configuration needed.

## AWS Bedrock

### Installation

```bash
pip install agenteval[bedrock]
```

### Configuration

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# Option 2: AWS CLI config
aws configure
```

### Example

```python
import json
import boto3

def create_agent():
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    
    def agent(prompt: str) -> str:
        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            }),
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
    
    return agent
```

## Anthropic

### Installation

```bash
pip install agenteval[anthropic]
```

### Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Example

```python
from anthropic import Anthropic

def create_agent():
    client = Anthropic()
    
    def agent(prompt: str) -> str:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    
    return agent
```

## Ollama (Local, $0)

### Installation

```bash
# Install agenteval
pip install agenteval[ollama]

# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2
```

### Configuration

No API keys needed. Ollama runs locally.

```bash
# Start Ollama server (if not already running)
ollama serve
```

### Example

```python
from ollama import chat

def create_agent():
    def agent(prompt: str) -> str:
        response = chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]
    
    return agent
```

## Auto-Detection

agenteval automatically detects which provider your agent uses by inspecting:

1. Imported packages (`openai`, `boto3`, `anthropic`, etc.)
2. Active network calls during agent execution
3. Model identifiers in API calls

You don't need to manually configure the interceptor — it's automatic.

## Using Providers for Evaluation

Some evaluators (e.g., `hallucination_score`, `semantic_similarity`) use an LLM-as-judge. Configure the evaluation provider:

```python
# conftest.py
import pytest
from agenteval.core.eval_model import EvalModel

@pytest.fixture
def eval_model():
    # Option 1: Use OpenAI for evals
    return EvalModel(provider="openai", model="gpt-4o-mini")
    
    # Option 2: Use local Ollama ($0)
    return EvalModel(provider="ollama", model="llama3.2")
```

See [$0 Local Evals](local-evals.md) for using Ollama as your eval provider to eliminate evaluation costs.

## Provider Priority

When multiple providers are available, agenteval auto-selects in this order:

1. **Agent provider** — Use the same provider the agent uses
2. **Explicit config** — `eval_model` fixture or `AGENTEVAL_EVAL_PROVIDER` env var
3. **Cheapest available** — Ollama → OpenAI (gpt-4o-mini) → Bedrock → others

Override with:

```bash
export AGENTEVAL_EVAL_PROVIDER="ollama"
export AGENTEVAL_EVAL_MODEL="llama3.2"
```

## Troubleshooting

### "Provider not detected"

**Problem**: agenteval can't detect which provider your agent uses.

**Solution**: Manually specify in `conftest.py`:

```python
@pytest.fixture
def agent(agent_runner: AgentRunner):
    my_agent = create_my_agent()
    return agent_runner.wrap(
        my_agent,
        name="my_agent",
        provider="openai",  # Explicit provider
    )
```

### "Missing credentials"

**Problem**: API key or credentials not found.

**Solution**: 
1. Check environment variables are set correctly
2. For AWS: ensure `~/.aws/credentials` is configured

### "Model not found"

**Problem**: Model ID not recognized by provider.

**Solution**: Check the provider's model catalog:
- OpenAI: https://platform.openai.com/docs/models
- Bedrock: `aws bedrock list-foundation-models`

## Next Steps

- [$0 Local Evals](local-evals.md) — Run evals with Ollama, no API cost
- [CI/CD Integration](ci-cd.md) — Configure cost limits and credentials for CI
- [Custom Evaluators](custom-evaluators.md) — Write provider-specific evaluators
