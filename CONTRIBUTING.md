# Contributing to agenteval

Thanks for your interest in contributing! agenteval is an open-source project and we welcome contributions of all kinds.

## Getting Started

### Development setup

```bash
# Clone the repo
git clone https://github.com/devbrat-anand/agenteval.git
cd agenteval

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dev dependencies
uv pip install -e ".[dev]" --system

# Verify setup
pytest tests/ -v
ruff check src/ tests/
mypy src/agenteval/
```

### Running tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_models.py -v

# With coverage
pytest tests/ --cov=agenteval --cov-report=term -v
```

### Code quality

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/agenteval/
```

## Contributing an Evaluator

The most impactful way to contribute. Here's how:

### 1. Create the evaluator

Create `src/agenteval/evaluators/your_evaluator.py`:

```python
"""Your evaluator description."""

from __future__ import annotations

from agenteval.core.models import EvalResult, Trace
from agenteval.evaluators.base import Evaluator


class YourEvaluator(Evaluator):
    """One-line description of what this evaluator checks."""

    name = "your_evaluator"

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        # Your evaluation logic
        score = 1.0
        passed = True
        reason = "Check passed"

        # Return an EvalResult
        return EvalResult(
            evaluator=self.name,
            score=score,
            passed=passed,
            reason=reason,
            details={},
        )
```

### 2. Register the entry point

Add to `pyproject.toml`:

```toml
[project.entry-points."agenteval.evaluators"]
your_evaluator = "agenteval.evaluators.your_evaluator:YourEvaluator"
```

### 3. Write tests

Create `tests/unit/test_your_evaluator.py`:

```python
from agenteval.core.models import Trace, Turn
from agenteval.evaluators.your_evaluator import YourEvaluator


def _make_trace(**overrides) -> Trace:
    defaults = {
        "agent_name": "test", "input": "query", "output": "answer",
        "turns": [], "total_cost_usd": 0.01, "total_latency_ms": 500,
        "total_input_tokens": 100, "total_output_tokens": 50, "metadata": {},
    }
    defaults.update(overrides)
    return Trace(**defaults)


def test_your_evaluator_passes():
    trace = _make_trace(output="good response")
    evaluator = YourEvaluator()
    result = evaluator.evaluate(trace)
    assert result.passed
    assert result.score > 0.0


def test_your_evaluator_fails():
    trace = _make_trace(output="bad response")
    evaluator = YourEvaluator()
    result = evaluator.evaluate(trace)
    assert not result.passed
```

### 4. Submit a PR

- Run `pytest tests/ -v` — all tests pass
- Run `ruff check src/ tests/` — no lint errors
- Run `mypy src/agenteval/` — no type errors
- Create a PR with a clear description

## Contributing an Interceptor

Provider interceptors capture LLM calls at the SDK or transport level.

### 1. Create the interceptor

Create `src/agenteval/interceptors/your_provider.py`:

```python
"""Your provider interceptor."""

from __future__ import annotations

from agenteval.core.models import LLMCall
from agenteval.interceptors.base import Interceptor


class YourProviderInterceptor(Interceptor):
    """Intercept calls to YourProvider SDK."""

    name = "your_provider"

    def install(self) -> None:
        """Monkey-patch or hook into the provider SDK."""
        # Hook into the SDK here
        pass

    def uninstall(self) -> None:
        """Restore original SDK behavior."""
        pass
```

### 2. Register in InterceptorRegistry

Add the auto-detect logic in `src/agenteval/interceptors/base.py`.

### 3. Add pricing data

Add model pricing to `src/agenteval/interceptors/pricing.json`.

## Issue Labels

| Label | Use for |
|---|---|
| `bug` | Something is broken |
| `enhancement` | New feature or improvement |
| `evaluator` | New evaluator proposal |
| `good-first-issue` | Good for newcomers |
| `documentation` | Documentation improvements |

## Code Style

- Python 3.10+, type hints everywhere
- `ruff` for linting and formatting
- `mypy` strict mode on public API
- Docstrings on all public functions
- Tests for all new code (TDD preferred)

## Pull Request Checklist

- [ ] Tests added/updated
- [ ] `ruff check` passes
- [ ] `mypy` passes
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow conventional commits

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
