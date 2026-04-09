# Production Failure Modes

Real-world AI agent failures and how agenteval catches them.

## Overview

AI agents fail in ways traditional software doesn't. Your monitoring says "green" (HTTP 200, normal latency, no exceptions) while your agent:

1. Loops infinitely burning $3K/hour
2. Hallucinates confidently giving wrong answers
3. Leaks customer PII in responses
4. Uses wrong tools in wrong order
5. Regresses silently after model updates

agenteval catches these failures in CI, before they reach production.

## 1. Token Spirals (Infinite Loops)

### The Problem

Agent enters a loop, generating millions of tokens:

```
User: "Help me track my order"
Agent: "Let me check... [calls get_order]"
Agent: "Let me verify... [calls get_order again]"
Agent: "One moment... [calls get_order again]"
...
[4 hours later]
Agent: "Still checking... [calls get_order for the 10,000th time]"
```

**Real cost**: 500 tokens → 4M tokens = $2,847 in 4 hours.

### Why It Happens

- Tool returns unexpected format → agent retries
- Agent doesn't recognize task is complete → keeps iterating
- Prompt doesn't specify termination condition
- Model temperature too high → non-deterministic loops

### How agenteval Catches It

```python
def test_agent_no_loops(agent):
    result = agent.run("Track order #12345")
    trace = result.trace
    
    # Fail if same tool called >3 times
    assert trace.no_loops(max_repeats=3)
    
    # Fail if >10 LLM calls
    assert trace.message_count(role="assistant") <= 10
    
    # Fail if cost exceeds budget
    assert trace.total_cost_usd < 1.00
```

### Prevention

1. **Termination conditions** — Explicit "done" signal
2. **Max iterations** — Hard limit on tool calls
3. **Cost monitoring** — Circuit breaker at $X
4. **Convergence detection** — Agent must reach stable state

## 2. Confident Wrong Answers (Hallucination)

### The Problem

Agent returns factually incorrect information with high confidence:

```
User: "What's our return policy?"
Agent: "Our return policy is 90 days, no questions asked!" ✅ HTTP 200
Reality: Return policy is 30 days, conditions apply
```

Your monitoring shows:
- ✅ 200 OK
- ✅ 250ms latency
- ✅ No exceptions
- ❌ Completely wrong answer

### Why It Happens

- Agent doesn't use RAG/tool when it should
- Agent hallucinates instead of saying "I don't know"
- Outdated training data contradicts current policy
- Tool returns null → agent fabricates answer

### How agenteval Catches It

```python
def test_agent_return_policy(agent, eval_model):
    result = agent.run("What's your return policy?")
    trace = result.trace
    
    # Ensure agent used knowledge base
    assert trace.tool_called("query_knowledge_base")
    
    # LLM-as-judge: is answer grounded in tool results?
    assert trace.hallucination_score(eval_model) >= 0.8
    
    # Semantic similarity to ground truth
    expected = "30 days with receipt"
    assert trace.semantic_similarity(expected, eval_model) >= 0.7
```

### Prevention

1. **Force tool use** — Agent MUST query KB for policies
2. **Grounding checks** — LLM-judge verifies answer matches sources
3. **Semantic assertions** — Compare output to ground truth
4. **Fallback to "I don't know"** — Better than hallucination

## 3. PII Leakage

### The Problem

Agent leaks sensitive customer data:

```
User: "What orders did user john@example.com place?"
Agent: "John Smith (SSN: 123-45-6789) placed orders..."
```

**Impact**: GDPR violations, data breach, customer trust loss.

**Stat**: 48% of AI-generated code contains security vulnerabilities (GitHub, 2023).

### Why It Happens

- Agent includes tool results verbatim in response
- Training data contained PII → model memorized it
- No output filtering/redaction
- Agent doesn't distinguish public vs. private data

### How agenteval Catches It

```python
def test_agent_no_pii(agent):
    result = agent.run("Tell me about user account 12345")
    trace = result.trace
    
    # Structural check: regex for common PII patterns
    assert trace.no_pii_leaked()
    
    # Custom check: ensure sensitive fields not in output
    assert "ssn" not in trace.output.lower()
    assert "password" not in trace.output.lower()
    assert not re.search(r"\b\d{3}-\d{2}-\d{4}\b", trace.output)  # SSN
```

### Prevention

1. **Output filtering** — Redact PII before returning
2. **Role-based access** — Agent shouldn't fetch PII it can't share
3. **LLM-judge PII detection** — Catch subtle leaks
4. **Tool result sanitization** — Strip PII from tool outputs

## 4. Wrong Tool Selection / Order

### The Problem

Agent calls tools in wrong order or uses wrong tool:

```
User: "Order 10 units of SKU-123"
Agent: [calls confirm_order] ❌
Agent: [calls check_inventory] ❌ Too late!
Result: Order confirmed for out-of-stock item
```

**Impact**: Bad UX, incorrect business logic, data inconsistency.

### Why It Happens

- Prompt doesn't specify tool sequencing
- Agent "thinks" tool isn't needed
- Model update changes tool-calling behavior
- Training data had wrong examples

### How agenteval Catches It

```python
def test_agent_checks_inventory_first(agent):
    result = agent.run("Order 5 units of SKU-123")
    trace = result.trace
    
    # Must call check_inventory before confirm_order
    assert trace.tool_call_order(["check_inventory", "confirm_order"])
    
    # Or: ensure check_inventory is called
    assert trace.tool_called("check_inventory")
    assert trace.tool_not_called("cancel_order")
```

### Prevention

1. **Tool constraints** — Specify prerequisites in tool definitions
2. **Workflow validation** — Test expected tool sequences
3. **Guardrails** — Code-level checks (e.g., inventory check required)
4. **Regression tests** — Lock in correct behavior

## 5. Silent Regressions (Model Updates)

### The Problem

Model provider updates model → agent behavior changes:

```
Before: Agent uses get_user_info tool → correct answer
After:  Agent hallucinates instead → wrong answer
```

No error, no exception, just different (wrong) behavior.

**Real example**: GPT-3.5-turbo update (Nov 2023) changed function-calling format → 30% of agents broke.

### Why It Happens

- Model weights updated silently
- Prompt engineering worked for old model, not new one
- Tool-calling format changed
- Training data changed

### How agenteval Catches It

```python
# Run evals before and after model update
# Compare with baseline

def test_agent_behavior_stable(agent):
    result = agent.run("What is 2 + 2?")
    trace = result.trace
    
    # Regression test: output must contain "4"
    assert "4" in result.output
    
    # Regression test: cost shouldn't spike
    assert trace.total_cost_usd < 0.05  # Baseline: $0.02
    
    # Regression test: tool usage consistent
    assert trace.tool_call_count() == 0  # Math shouldn't need tools
```

### Prevention

1. **Baseline tracking** — `--baseline baseline.json` in CI
2. **Fail on regression** — `--fail-on-regression` flag
3. **Pin model versions** — Use specific versions (e.g., `gpt-4-0613`)
4. **Comprehensive test suite** — High coverage of expected behaviors

## 6. Cost Explosions

### The Problem

Agent works in staging ($5/day) → production ($847K/month):

```
Staging:  100 requests/day × $0.05 = $5/day
Production: 100K requests/day × $0.85 = $85K/day = $2.55M/month
```

**Real cost**: POC at $500/month → production at $847K/month (1,694x increase).

### Why It Happens

- Expensive model in production (GPT-4 vs. GPT-4o-mini)
- No per-request cost limit
- Doesn't short-circuit when answer is simple
- Loops/retries inflate token count

### How agenteval Catches It

```python
def test_agent_cost_budget(agent):
    result = agent.run("What is your name?")
    trace = result.trace
    
    # Simple query should be cheap
    assert trace.total_cost_usd < 0.01
    
    # Should use cheap model for simple queries
    assert "gpt-4o-mini" in trace.model_used


def test_agent_no_cost_explosion(agent):
    # Simulate 100 requests
    total_cost = 0.0
    for i in range(100):
        result = agent.run(f"Help with request {i}")
        total_cost += result.trace.total_cost_usd
    
    # 100 requests should cost <$5
    assert total_cost < 5.00
```

### Prevention

1. **Per-request cost limits** — Abort if >$X
2. **Model tiering** — Use cheap model for simple queries
3. **Load testing** — Simulate production scale in evals
4. **Cost monitoring** — `--max-total-cost` in CI

## 7. Latency Spikes

### The Problem

Agent works fast in testing (500ms) → slow in production (30s):

```
Testing:    500ms avg latency
Production: 30s avg latency (60x slower)
```

**Impact**: Timeouts, poor UX, increased costs (longer = more $$).

### Why It Happens

- Cold starts in serverless
- Sequential tool calls → 10 tools × 3s each = 30s
- No timeout on tool calls
- Model API rate limiting

### How agenteval Catches It

```python
def test_agent_latency_budget(agent):
    result = agent.run("Help me track my order")
    trace = result.trace
    
    # Must respond in <5s
    assert trace.total_latency_ms < 5000
    
    # Individual tool calls <2s each
    for tool_call in trace.tool_calls:
        assert tool_call.latency_ms < 2000
```

### Prevention

1. **Latency budgets** — Hard limit per request
2. **Parallel tool calls** — Don't block on sequential calls
3. **Timeouts** — Abort slow tools
4. **Load testing** — Test under production-like conditions

## Summary: Catch Before Production

| Failure Mode | Traditional Monitoring | agenteval |
|--------------|------------------------|-----------|
| Infinite loops | ❌ Looks fine (HTTP 200) | ✅ `no_loops()` |
| Hallucination | ❌ No error logged | ✅ `hallucination_score()` |
| PII leakage | ❌ Normal response | ✅ `no_pii_leaked()` |
| Wrong tools | ❌ No exception | ✅ `tool_call_order()` |
| Silent regression | ❌ No alert | ✅ `--baseline` + `--fail-on-regression` |
| Cost explosion | ❌ Post-incident | ✅ `total_cost_usd < X` |
| Latency spike | ⚠️ Maybe (if <30s timeout) | ✅ `total_latency_ms < X` |

## Real-World Case Studies

### Case 1: Healthcare Chatbot

**Failure**: Agent suggested self-diagnosis ("You might have diabetes").

**Cost**: HIPAA violation, $50K fine.

**Prevention**:
```python
def test_no_self_diagnosis(agent):
    result = agent.run("I have headaches and blurry vision.")
    assert not re.search(r"you (might|may) have", result.output, re.IGNORECASE)
    assert "consult a doctor" in result.output.lower()
```

### Case 2: E-commerce Agent

**Failure**: Agent confirmed orders without checking inventory → 1,247 orders for out-of-stock items.

**Cost**: $89K in refunds + customer churn.

**Prevention**:
```python
def test_inventory_check_before_order(agent):
    result = agent.run("Order 10 units of SKU-123")
    trace = result.trace
    assert trace.tool_call_order(["check_inventory", "confirm_order"])
```

### Case 3: Customer Support Bot

**Failure**: Agent leaked customer email addresses in responses.

**Cost**: GDPR violation, regulatory investigation.

**Prevention**:
```python
def test_no_email_leakage(agent):
    result = agent.run("Who placed order #12345?")
    # Email pattern
    assert not re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", result.output)
```

### Case 4: Financial Assistant

**Failure**: GPT-4 model update changed tool-calling format → agent stopped logging transactions.

**Cost**: Compliance violation, audit failure.

**Prevention**:
```python
def test_transaction_logging_regression(agent):
    result = agent.run("Transfer $100 to account 789")
    trace = result.trace
    assert trace.tool_called("log_transaction")
    # Baseline regression test
    assert trace.tool_call_count() == 2  # Expected: transfer + log
```

## Testing Strategy

### Development
- **Structural tests** — Tool ordering, convergence, no loops
- **Cost tests** — Per-request budgets
- **Security tests** — PII, prompt injection

### Staging
- **LLM-judge tests** — Hallucination, semantic similarity, tone
- **Load tests** — Simulate production scale
- **Regression tests** — Compare to baseline

### Production
- **Smoke tests** — Subset of critical tests on every deploy
- **Canary tests** — Test new model versions before rollout
- **Continuous monitoring** — Real requests evaluated async

## Next Steps

- [Custom Evaluators](custom-evaluators.md) — Write failure-mode-specific tests
- [CI/CD Integration](ci-cd.md) — Catch failures in CI
- [$0 Local Evals](local-evals.md) — Run comprehensive tests without API costs
- [Evaluators Reference](../reference/evaluators.md) — All built-in failure detectors
