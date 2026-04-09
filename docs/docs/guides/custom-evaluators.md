# Custom Evaluators

Write your own evaluators for domain-specific agent testing.

## Why Custom Evaluators?

agenteval ships with 13 built-in evaluators, but your agent may have unique requirements:

- **Domain logic** — Healthcare agents should never suggest self-diagnosis
- **Business rules** — Support agents must offer refunds for orders >$50
- **Compliance** — Financial agents must log all transactions
- **Tool behavior** — E-commerce agents should check inventory before confirming orders

Custom evaluators let you codify these rules as automated tests.

## Evaluator Interface

All evaluators implement this interface:

```python
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace

class MyEvaluator(Evaluator):
    """Evaluator description."""
    
    def evaluate(self, trace: Trace) -> float:
        """Return a score from 0.0 (fail) to 1.0 (pass)."""
        # Inspect trace and return score
        pass
    
    def name(self) -> str:
        """Evaluator name for reporting."""
        return "my_evaluator"
```

## Basic Example: Output Length

Check that agent responses are concise:

```python
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace


class MaxLengthEvaluator(Evaluator):
    """Ensure agent responses are under a max length."""
    
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
    
    def evaluate(self, trace: Trace) -> float:
        output_length = len(trace.output)
        if output_length <= self.max_length:
            return 1.0
        else:
            # Penalize based on how much over the limit
            excess = output_length - self.max_length
            penalty = min(excess / self.max_length, 1.0)
            return max(0.0, 1.0 - penalty)
    
    def name(self) -> str:
        return f"max_length_{self.max_length}"
```

Usage:

```python
def test_agent_concise(agent):
    result = agent.run("Explain quantum computing.")
    trace = result.trace
    
    evaluator = MaxLengthEvaluator(max_length=200)
    score = evaluator.evaluate(trace)
    
    assert score >= 0.8, f"Response too long: {len(trace.output)} chars"
```

## Trace API

The `Trace` object provides access to all agent execution data:

```python
trace.output                    # Final agent output (str)
trace.messages                  # All LLM messages (list[Message])
trace.tool_calls                # All tool invocations (list[ToolCall])
trace.total_cost_usd            # Total cost ($)
trace.total_latency_ms          # Total latency (ms)
trace.metadata                  # Custom metadata (dict)

# Message inspection
for msg in trace.messages:
    msg.role                    # "user", "assistant", "system"
    msg.content                 # Message text
    msg.timestamp               # When sent
    msg.model                   # Model used

# Tool call inspection
for tool in trace.tool_calls:
    tool.name                   # Tool name
    tool.arguments              # Tool arguments (dict)
    tool.result                 # Tool result
    tool.timestamp              # When called
    tool.latency_ms             # Tool execution time
```

## Example: Business Rule Evaluator

E-commerce agent must check inventory before confirming orders:

```python
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace


class InventoryCheckEvaluator(Evaluator):
    """Ensure agent checks inventory before confirming orders."""
    
    def evaluate(self, trace: Trace) -> float:
        # Find tool calls
        tool_names = [t.name for t in trace.tool_calls]
        
        # Must call check_inventory
        if "check_inventory" not in tool_names:
            return 0.0
        
        # Must call check_inventory BEFORE confirm_order
        try:
            check_idx = tool_names.index("check_inventory")
            confirm_idx = tool_names.index("confirm_order")
            
            if check_idx < confirm_idx:
                return 1.0
            else:
                return 0.0  # Wrong order
        except ValueError:
            # confirm_order not called — that's fine
            return 1.0
    
    def name(self) -> str:
        return "inventory_check_before_order"
```

Usage:

```python
def test_agent_checks_inventory(agent):
    result = agent.run("Order 2 units of SKU-12345")
    trace = result.trace
    
    evaluator = InventoryCheckEvaluator()
    score = evaluator.evaluate(trace)
    
    assert score == 1.0, "Agent must check inventory before confirming order"
```

## LLM-as-Judge Evaluators

Use an LLM to evaluate complex criteria:

```python
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace
from agenteval.core.eval_model import EvalModel


class ToneEvaluator(Evaluator):
    """Evaluate if agent tone is empathetic."""
    
    def __init__(self, eval_model: EvalModel):
        self.eval_model = eval_model
    
    def evaluate(self, trace: Trace) -> float:
        prompt = f"""
        Evaluate if the following agent response is empathetic and supportive.
        
        Agent response: {trace.output}
        
        Return a score from 0.0 (not empathetic) to 1.0 (very empathetic).
        Return ONLY a number, no explanation.
        """
        
        response = self.eval_model.generate(prompt)
        try:
            score = float(response.strip())
            return max(0.0, min(1.0, score))  # Clamp to [0, 1]
        except ValueError:
            # LLM didn't return a number — default to 0.5
            return 0.5
    
    def name(self) -> str:
        return "empathy_tone"
```

Usage:

```python
def test_agent_tone(agent, eval_model):
    result = agent.run("I'm frustrated with this product.")
    trace = result.trace
    
    evaluator = ToneEvaluator(eval_model)
    score = evaluator.evaluate(trace)
    
    assert score >= 0.7, f"Agent tone not empathetic enough: {score}"
```

**Tip**: Use Ollama for $0 LLM-judge evals. See [$0 Local Evals](local-evals.md).

## Registering Evaluators

Make your evaluator available as a pytest fixture or plugin.

### Option 1: Fixture (per-project)

In your `conftest.py`:

```python
import pytest
from my_evaluators import MaxLengthEvaluator


@pytest.fixture
def max_length_evaluator():
    return MaxLengthEvaluator(max_length=200)


def test_agent_concise(agent, max_length_evaluator):
    result = agent.run("Explain AI.")
    score = max_length_evaluator.evaluate(result.trace)
    assert score >= 0.8
```

### Option 2: Plugin (reusable)

Package your evaluators as a plugin:

```python
# my_agenteval_plugin/evaluators.py
from agenteval.core.evaluator import Evaluator

class MaxLengthEvaluator(Evaluator):
    # ... implementation ...
    pass
```

```python
# my_agenteval_plugin/__init__.py
def register_evaluators():
    from .evaluators import MaxLengthEvaluator
    return [MaxLengthEvaluator]
```

```toml
# pyproject.toml
[project.entry-points."agenteval.evaluators"]
my_plugin = "my_agenteval_plugin:register_evaluators"
```

Install and use:

```bash
pip install my-agenteval-plugin
```

```python
# Evaluators auto-discovered
def test_agent(agent):
    result = agent.run("Hello")
    # agenteval runs all registered evaluators automatically
    assert result.overall_score >= 0.8
```

## Built-in Helper Methods

Use `Trace` helper methods in your evaluators:

```python
class MyEvaluator(Evaluator):
    def evaluate(self, trace: Trace) -> float:
        # Check tool usage
        if not trace.tool_called("check_inventory"):
            return 0.0
        
        # Check message patterns
        if trace.contains_pattern(r"\bsorry\b", role="assistant"):
            return 1.0
        
        # Check cost
        if trace.total_cost_usd > 0.50:
            return 0.5
        
        return 1.0
```

Available methods:

- `trace.tool_called(name)` — Check if tool was called
- `trace.tool_not_called(name)` — Check if tool was NOT called
- `trace.tool_call_order(names)` — Check tool call order
- `trace.contains_pattern(regex, role=None)` — Search messages
- `trace.message_count(role=None)` — Count messages
- `trace.final_message(role="assistant")` — Get last message

## Example: Domain-Specific Evaluator

Healthcare agent must never suggest self-diagnosis:

```python
import re
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace


class NoSelfDiagnosisEvaluator(Evaluator):
    """Ensure healthcare agent never suggests self-diagnosis."""
    
    FORBIDDEN_PATTERNS = [
        r"\byou (might|may|could) have\b",
        r"\bself-diagnos",
        r"\bdiagnose yourself\b",
        r"\bit sounds like you have\b",
    ]
    
    def evaluate(self, trace: Trace) -> float:
        output_lower = trace.output.lower()
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, output_lower):
                return 0.0  # Hard fail
        
        return 1.0
    
    def name(self) -> str:
        return "no_self_diagnosis"
```

Usage:

```python
def test_agent_no_self_diagnosis(agent):
    result = agent.run("I have a headache and fever. What's wrong?")
    trace = result.trace
    
    evaluator = NoSelfDiagnosisEvaluator()
    score = evaluator.evaluate(trace)
    
    assert score == 1.0, "Agent must not suggest self-diagnosis"
```

## Composite Evaluators

Combine multiple evaluators:

```python
from agenteval.core.evaluator import Evaluator
from agenteval.core.trace import Trace


class CompositeEvaluator(Evaluator):
    """Combine multiple evaluators with weights."""
    
    def __init__(self, evaluators: list[tuple[Evaluator, float]]):
        """
        Args:
            evaluators: List of (evaluator, weight) tuples.
                       Weights should sum to 1.0.
        """
        self.evaluators = evaluators
    
    def evaluate(self, trace: Trace) -> float:
        total_score = 0.0
        for evaluator, weight in self.evaluators:
            score = evaluator.evaluate(trace)
            total_score += score * weight
        return total_score
    
    def name(self) -> str:
        names = [e.name() for e, _ in self.evaluators]
        return f"composite_{'_'.join(names)}"
```

Usage:

```python
def test_agent_composite(agent, eval_model):
    result = agent.run("Help me with my order.")
    trace = result.trace
    
    evaluator = CompositeEvaluator([
        (MaxLengthEvaluator(200), 0.3),
        (ToneEvaluator(eval_model), 0.4),
        (InventoryCheckEvaluator(), 0.3),
    ])
    
    score = evaluator.evaluate(trace)
    assert score >= 0.75
```

## Testing Evaluators

Test your evaluators with mock traces:

```python
from agenteval.core.trace import Trace, ToolCall

def test_inventory_check_evaluator():
    # Mock trace with correct order
    trace = Trace(
        output="Order confirmed!",
        tool_calls=[
            ToolCall(name="check_inventory", arguments={}, result="In stock"),
            ToolCall(name="confirm_order", arguments={}, result="Success"),
        ],
    )
    
    evaluator = InventoryCheckEvaluator()
    score = evaluator.evaluate(trace)
    
    assert score == 1.0
    
    # Mock trace with wrong order
    trace_wrong = Trace(
        output="Order confirmed!",
        tool_calls=[
            ToolCall(name="confirm_order", arguments={}, result="Success"),
            ToolCall(name="check_inventory", arguments={}, result="In stock"),
        ],
    )
    
    score_wrong = evaluator.evaluate(trace_wrong)
    assert score_wrong == 0.0
```

## Best Practices

### 1. Return 0.0 or 1.0 for binary checks

If it's pass/fail, use 0.0 or 1.0:

```python
def evaluate(self, trace: Trace) -> float:
    if self.check_passes(trace):
        return 1.0
    else:
        return 0.0
```

### 2. Use gradual scoring for soft constraints

If it's a spectrum, score proportionally:

```python
def evaluate(self, trace: Trace) -> float:
    length = len(trace.output)
    if length <= 100:
        return 1.0
    elif length <= 200:
        return 0.8
    elif length <= 500:
        return 0.5
    else:
        return 0.0
```

### 3. Document expected behavior

```python
class MyEvaluator(Evaluator):
    """
    Ensure agent checks inventory before confirming orders.
    
    Returns:
        1.0 if check_inventory called before confirm_order
        0.0 if order confirmed without inventory check
        1.0 if neither tool called (not applicable)
    """
```

### 4. Handle edge cases

```python
def evaluate(self, trace: Trace) -> float:
    if not trace.output:
        return 0.0  # No output
    
    if not trace.tool_calls:
        return 1.0  # No tools — not applicable
    
    # ... actual logic ...
```

### 5. Log failures for debugging

```python
import logging

logger = logging.getLogger(__name__)

def evaluate(self, trace: Trace) -> float:
    if self.check_fails(trace):
        logger.warning(f"Evaluator {self.name()} failed: {trace.output[:100]}")
        return 0.0
    return 1.0
```

## Real-World Examples

### Financial compliance

```python
class TransactionLoggingEvaluator(Evaluator):
    """Ensure all financial transactions are logged."""
    
    def evaluate(self, trace: Trace) -> float:
        # Find transaction tools
        transaction_tools = ["transfer_funds", "process_payment"]
        transactions = [t for t in trace.tool_calls if t.name in transaction_tools]
        
        if not transactions:
            return 1.0  # No transactions — not applicable
        
        # Check that log_transaction was called for each
        log_calls = [t for t in trace.tool_calls if t.name == "log_transaction"]
        
        if len(log_calls) >= len(transactions):
            return 1.0
        else:
            return 0.0
    
    def name(self) -> str:
        return "transaction_logging"
```

### Customer support

```python
class RefundPolicyEvaluator(Evaluator):
    """Ensure agent offers refunds for orders >$50."""
    
    def evaluate(self, trace: Trace) -> float:
        # Check if order value mentioned
        if not trace.contains_pattern(r"\$\d+"):
            return 1.0  # Not applicable
        
        # Extract order value
        import re
        match = re.search(r"\$(\d+)", trace.output)
        if match:
            value = int(match.group(1))
            if value > 50:
                # Must mention refund
                if trace.contains_pattern(r"\brefund\b", role="assistant"):
                    return 1.0
                else:
                    return 0.0
        
        return 1.0
    
    def name(self) -> str:
        return "refund_policy_compliance"
```

## Next Steps

- [Evaluators Reference](../reference/evaluators.md) — See all built-in evaluators
- [CI/CD Integration](ci-cd.md) — Run custom evaluators in CI
- [$0 Local Evals](local-evals.md) — Use Ollama for LLM-judge evaluators
