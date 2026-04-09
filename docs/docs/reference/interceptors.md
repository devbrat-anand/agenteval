# Interceptors Reference

Complete reference for LLM provider interceptors in agenteval.

## Overview

Interceptors automatically capture LLM API calls from your agent for tracing, cost calculation, and evaluation. No manual instrumentation required.

## Supported Providers

| Provider | SDK | Auto-Detection | Cost Tracking | Hook Method |
|----------|-----|----------------|---------------|-------------|
| OpenAI | `openai` | ✅ | ✅ | Monkey-patch |
| AWS Bedrock | `boto3` | ✅ | ✅ | Boto3 events |
| Anthropic | `anthropic` | ✅ | ✅ | Wrapper injection |

## How Interceptors Work

1. **Auto-detection**: agenteval detects which SDK your agent imports
2. **Hook injection**: Intercepts API calls transparently
3. **Trace capture**: Records messages, tool calls, costs, latency
4. **No changes needed**: Your agent code runs unchanged

```python
# Your agent code (unchanged)
from openai import OpenAI

def my_agent(prompt: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# agenteval automatically intercepts the OpenAI call
```

## OpenAI Interceptor

### Supported SDKs
- `openai>=1.0.0` (official Python SDK)

### What's Captured

```python
{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "messages": [...],
    "tools": [...],  # If function calling used
    "input_tokens": 120,
    "output_tokens": 45,
    "cost_usd": 0.000825,
    "latency_ms": 847,
}
```

### Hook Mechanism

Monkey-patches `openai.chat.completions.create()`:

```python
# Original call
response = client.chat.completions.create(...)

# Intercepted as:
response = agenteval_intercepted_create(...)
```

### Configuration

Auto-enabled when `openai` is imported. Disable with:

```python
import os
os.environ["AGENTEVAL_DISABLE_OPENAI"] = "1"
```

### Cost Calculation

Based on official OpenAI pricing:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |

Pricing updated: January 2025

---

## AWS Bedrock Interceptor

### Supported SDKs
- `boto3>=1.28.0` with `bedrock-runtime` client

### What's Captured

```python
{
    "provider": "bedrock",
    "model": "anthropic.claude-3-haiku-20240307-v1:0",
    "messages": [...],
    "input_tokens": 95,
    "output_tokens": 203,
    "cost_usd": 0.000156,
    "latency_ms": 1432,
}
```

### Hook Mechanism

Uses boto3 event system:

```python
# Hooks into before-call and after-call events
client.meta.events.register('before-call.bedrock-runtime.InvokeModel', ...)
client.meta.events.register('after-call.bedrock-runtime.InvokeModel', ...)
```

### Configuration

Auto-enabled when `boto3` client for `bedrock-runtime` is created. Disable with:

```python
os.environ["AGENTEVAL_DISABLE_BEDROCK"] = "1"
```

### Cost Calculation

Based on AWS Bedrock pricing by region:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |
| Llama 3.1 70B | $0.99 | $0.99 |
| Llama 3.1 8B | $0.22 | $0.22 |

Pricing for us-east-1, updated: January 2025

---

## Anthropic Interceptor

### Supported SDKs
- `anthropic>=0.18.0`

### What's Captured

```python
{
    "provider": "anthropic",
    "model": "claude-3-haiku-20240307",
    "messages": [...],
    "input_tokens": 110,
    "output_tokens": 89,
    "cost_usd": 0.000342,
    "latency_ms": 1089,
}
```

### Hook Mechanism

Wraps `client.messages.create()`:

```python
# Original
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(...)

# Intercepted
response = agenteval_wrapped_create(...)
```

### Configuration

Auto-enabled when `anthropic` is imported. Disable with:

```python
os.environ["AGENTEVAL_DISABLE_ANTHROPIC"] = "1"
```

### Cost Calculation

Based on Anthropic pricing:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

Pricing updated: January 2025

---

## PricingEngine

The `PricingEngine` calculates costs based on token counts and model IDs.

### Usage

```python
from agenteval.core.pricing import PricingEngine

engine = PricingEngine()

cost = engine.calculate_cost(
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
)
# Returns: 0.000045 (USD)
```

### Custom Pricing

Override pricing for custom models:

```python
engine = PricingEngine()
engine.add_model(
    model_id="my-custom-model",
    input_price_per_1m=1.00,
    output_price_per_1m=2.00,
)
```

Or via environment variable:

```bash
export AGENTEVAL_CUSTOM_PRICING='{"my-model": {"input": 1.0, "output": 2.0}}'
```

### Model Aliases

PricingEngine resolves model aliases:

```python
# All resolve to same pricing:
"gpt-4o-mini"
"gpt-4o-mini-2024-07-18"
"gpt-4o-mini-latest"
```

### Pricing Updates

Update pricing database:

```bash
agenteval pricing update
```

Or manually:

```python
from agenteval.core.pricing import PricingEngine

engine = PricingEngine()
engine.refresh_pricing()  # Fetches latest from providers
```

---

## Auto-Detection

agenteval auto-detects providers by:

1. **Import inspection**: Checks which SDKs are imported
2. **Client type**: Checks client class type

### Priority Order

If multiple providers detected:

1. Explicit config: `AGENTEVAL_PROVIDER=openai`
2. Most recently used
3. First detected

### Force Provider

```python
os.environ["AGENTEVAL_PROVIDER"] = "openai"
```

Or in `conftest.py`:

```python
@pytest.fixture
def agent(agent_runner: AgentRunner):
    my_agent = create_my_agent()
    return agent_runner.wrap(my_agent, name="my_agent", provider="openai")
```

---

## Trace Structure

All interceptors produce traces in this format:

```python
{
    "trace_id": "uuid-...",
    "agent_name": "my_agent",
    "input": "User prompt",
    "output": "Agent response",
    "messages": [
        {
            "role": "user",
            "content": "User prompt",
            "timestamp": "2025-01-15T10:30:00Z",
        },
        {
            "role": "assistant",
            "content": "Agent response",
            "timestamp": "2025-01-15T10:30:02Z",
            "model": "gpt-4o-mini",
            "input_tokens": 120,
            "output_tokens": 45,
            "cost_usd": 0.000825,
            "latency_ms": 847,
        },
    ],
    "tool_calls": [
        {
            "name": "get_weather",
            "arguments": {"city": "NYC"},
            "result": "72F, sunny",
            "timestamp": "2025-01-15T10:30:01Z",
            "latency_ms": 234,
        },
    ],
    "total_cost_usd": 0.000825,
    "total_latency_ms": 2000,
    "metadata": {...},
}
```

---

## Troubleshooting

### "Provider not detected"

**Problem**: agenteval can't detect which provider you're using.

**Solution**:
```python
# Explicitly specify provider
@pytest.fixture
def agent(agent_runner: AgentRunner):
    my_agent = create_my_agent()
    return agent_runner.wrap(my_agent, provider="openai")
```

### "Cost is $0.00"

**Problem**: Cost not calculated correctly.

**Causes**:
1. Local model (Ollama) — cost is actually $0
2. Custom model not in pricing DB
3. Token count not returned by provider

**Solution**:
```python
# Add custom pricing
from agenteval.core.pricing import PricingEngine
engine = PricingEngine()
engine.add_model("my-model", input_price_per_1m=1.0, output_price_per_1m=2.0)
```

### "Interceptor conflicts with other tools"

**Problem**: agenteval interceptor conflicts with LangSmith, Weights & Biases, etc.

**Solution**:
1. Load agenteval last (after other tools)
2. Or disable conflicting interceptor:
```python
os.environ["AGENTEVAL_DISABLE_OPENAI"] = "1"
```

### "Missing token counts"

**Problem**: Trace shows 0 tokens but API was called.

**Causes**:
1. Provider doesn't return token counts (rare)
2. Streaming mode (not fully supported)

**Solution**:
```python
# Estimate tokens if not provided
trace.estimate_tokens = True
```

---

## Advanced: Custom Interceptors

Write your own interceptor for custom providers:

```python
from agenteval.core.interceptor import Interceptor
from agenteval.core.trace import Trace, Message


class MyProviderInterceptor(Interceptor):
    """Intercept MyProvider API calls."""
    
    def detect(self) -> bool:
        """Return True if this provider should be used."""
        try:
            import myprovider
            return True
        except ImportError:
            return False
    
    def install_hooks(self):
        """Install hooks to intercept API calls."""
        import myprovider
        
        original_call = myprovider.Client.call
        
        def wrapped_call(self, *args, **kwargs):
            start = time.time()
            response = original_call(self, *args, **kwargs)
            latency = (time.time() - start) * 1000
            
            # Record in trace
            self.trace.add_message(Message(
                role="assistant",
                content=response.text,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_ms=latency,
            ))
            
            return response
        
        myprovider.Client.call = wrapped_call
    
    def provider_name(self) -> str:
        return "myprovider"
```

Register via entry point:

```toml
# pyproject.toml
[project.entry-points."agenteval.interceptors"]
myprovider = "my_interceptor:MyProviderInterceptor"
```

---

## Next Steps

- [Provider Setup](../guides/providers.md) — Configure provider credentials
- [Custom Evaluators](../guides/custom-evaluators.md) — Use trace data in evaluators
- [Evaluators Reference](evaluators.md) — What you can do with traces
