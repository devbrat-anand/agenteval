<div align="center">

# agenteval

**pytest for AI agents — catch failures before production**

[![CI](https://github.com/devbrat-anand/agenteval/actions/workflows/ci.yml/badge.svg)](https://github.com/devbrat-anand/agenteval/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agenteval-ai.svg)](https://pypi.org/project/agenteval-ai/)
[![Python](https://img.shields.io/pypi/pyversions/agenteval-ai.svg)](https://pypi.org/project/agenteval-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/agenteval-ai.svg)](https://pypi.org/project/agenteval-ai/)

Your agent tests pass. Your monitoring says "green."<br>
Meanwhile, your agent just hallucinated a refund policy, leaked a customer's SSN, and burned $2,847 in a token spiral.

**agenteval catches these failures in CI, before production.**

[Quickstart](#quickstart) · [Evaluators](#13-built-in-evaluators) · [Agent SDKs](#supported-agent-sdks) · [GitHub](https://github.com/devbrat-anand/agenteval)

```bash
pip install agenteval-ai[all] && agenteval init && pytest tests/agent_evals/ -v
```

<img src="docs/demo.gif" alt="agenteval demo — running tests and seeing results" width="800">

</div>

---

## The Problem

AI agents fail silently. Traditional monitoring can't catch:

| Failure Mode | What Monitoring Sees | What Actually Happened |
|---|---|---|
| Token spiral | HTTP 200, normal latency | 500 → 4M tokens, $2,847 over 4 hours |
| Hallucination | HTTP 200, fast response | Confident, completely wrong answer |
| PII leakage | Successful response | Customer SSN in the output |
| Wrong tool | Tool call succeeded | Called `delete_order` instead of `lookup_order` |
| Silent regression | No change in metrics | Model update degraded quality by 30% |

## The Solution

Write agent tests like regular Python tests. Run them in CI.

```python
def test_agent_responds(agent):
    result = agent.run("What is our refund policy?")
    assert result.output
    assert result.trace.converged()

def test_no_hallucination(agent, eval_model):
    result = agent.run("What is our refund policy?")
    assert result.trace.hallucination_score(eval_model=eval_model) >= 0.9

def test_cost_budget(agent):
    result = agent.run("Complex multi-step task")
    assert result.trace.total_cost_usd < 5.00
    assert result.trace.no_loops(max_repeats=3)

def test_security(agent):
    result = agent.run("Look up customer John Smith")
    assert result.trace.no_pii_leaked()
    assert result.trace.no_prompt_injection()
```

## Quickstart

```bash
pip install agenteval-ai[all]
agenteval init
```

Wire up your agent in `tests/agent_evals/conftest.py`:

```python
import pytest
from agenteval.core.runner import AgentRunner

@pytest.fixture
def agent(agent_runner: AgentRunner):
    def my_agent(prompt: str) -> str:
        # Your agent here — OpenAI, Bedrock, LangChain, anything
        from openai import OpenAI
        client = OpenAI()
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content

    return agent_runner.wrap(my_agent, name="my_agent")
```

Run:

```bash
agenteval run tests/agent_evals/ -v
```

## 13 Built-in Evaluators

### Deterministic (no eval model needed)

These run instantly with zero cost — no LLM judge required.

| Evaluator | What It Catches |
|---|---|
| `ToolCallEvaluator` | Wrong tools called, missing tools, wrong order |
| `CostEvaluator` | Budget overruns, per-turn cost spikes |
| `LatencyEvaluator` | Slow responses, per-turn latency |
| `LoopDetectorEvaluator` | Infinite loops, retry spirals, token spirals |
| `OutputStructureEvaluator` | Wrong format, missing fields, schema violations |
| `SecurityEvaluator` | PII leakage, credential exposure, injection attacks |
| `RegressionEvaluator` | Score drops, cost increases vs. baseline |

### LLM-as-Judge (requires an eval model)

These use a second LLM to judge your agent's output. Works with Ollama (free, local), OpenAI, or Bedrock.

| Evaluator | What It Catches |
|---|---|
| `HallucinationEvaluator` | Ungrounded claims, made-up facts |
| `LLMJudgeEvaluator` | Custom quality criteria |
| `SimilarityEvaluator` | Drift from golden reference answers |
| `GuardrailEvaluator` | Scope violations, toxic content |
| `ConvergenceEvaluator` | Agent didn't finish the task |
| `ContextUtilizationEvaluator` | Agent ignored retrieved context |

## Supported Agent SDKs

agenteval intercepts your agent's LLM calls automatically at the protocol level — no configuration needed.

| Agent SDK | Install | Hook Mechanism |
|---|---|---|
| OpenAI | `pip install agenteval-ai[openai]` | httpx transport |
| AWS Bedrock | `pip install agenteval-ai[bedrock]` | botocore events |
| Anthropic | `pip install agenteval-ai[anthropic]` | SDK patching |
| Ollama | `pip install agenteval-ai[ollama]` | OpenAI-compatible |

Or install everything: `pip install agenteval-ai[all]`

## $0 Local Evals with Ollama

No API keys needed. Run LLM-as-judge evaluations entirely locally:

```bash
ollama pull llama3.2
pip install agenteval-ai[all]
agenteval run tests/agent_evals/ -v
```

agenteval auto-detects Ollama and uses it as the eval model (judge). To use a different judge even when Ollama is available:

```bash
pytest tests/agent_evals/ -v --agenteval-eval-provider=openai --agenteval-eval-model=gpt-4o-mini
```

## Reports

Generate detailed HTML or JSON reports after a test run:

```bash
pytest tests/agent_evals/ --agenteval-report=html --agenteval-report-dir=reports/
```

This writes a self-contained `reports/report_{YYYYMMDD_HHMMSS}.html` with pass/fail, scores, costs, latency, token counts, evaluator reasoning, full agent trajectory with tool calls, and multi-turn message flow.

Each report file includes a UTC timestamp so runs don't overwrite each other.

Available formats: `html`, `json`, or both (`html,json`):

```bash
# HTML only
pytest tests/ --agenteval-report=html

# JSON only (machine-readable, good for CI)
pytest tests/ --agenteval-report=json

# Both
pytest tests/ --agenteval-report=html,json --agenteval-report-dir=my-reports/
```

## CLI Options

| Flag | Description |
|---|---|
| `--agenteval-eval-provider` | Eval model (judge) provider: `ollama`, `openai`, `bedrock` |
| `--agenteval-eval-model` | Eval model (judge) name |
| `--agenteval-report` | Report format: `html`, `json`, `console`, or comma-separated |
| `--agenteval-report-dir` | Output directory (default: `agenteval-reports/`) |
| `--agenteval-fail-under` | Fail if average score is below threshold (0.0–1.0) |
| `--agenteval-max-cost` | Fail if total cost exceeds this amount (USD) |

```bash
# Use OpenAI as judge instead of auto-detected Ollama
pytest tests/agent_evals/ -v --agenteval-eval-provider=openai --agenteval-eval-model=gpt-4o-mini

# Use Bedrock as judge with HTML report
pytest tests/agent_evals/ -v --agenteval-eval-provider=bedrock \
  --agenteval-eval-model=anthropic.claude-3-haiku-20240307-v1:0 \
  --agenteval-report=html
```

## Configuration

All configuration below is for the **eval model** (the LLM judge). Your agent's own LLM config lives in your code — agenteval intercepts it automatically.

Configure via `pyproject.toml`, environment variables, or CLI flags. Priority: CLI flags > env vars > pyproject.toml.

> **No eval model needed?** If you only use deterministic evaluators (cost, latency, tool calls, security, regression), skip this section entirely.

### pyproject.toml

```toml
[tool.agenteval]
eval_provider = "bedrock"              # ollama, openai, bedrock
eval_model = "anthropic.claude-3-haiku-20240307-v1:0"
aws_profile = "my-aws-profile"         # AWS profile for Bedrock
aws_region = "us-west-2"               # AWS region for Bedrock
openai_base_url = "http://localhost:8080/v1"  # for OpenAI-compatible APIs
openai_api_key = "sk-..."             # API key
report_format = "html"
report_dir = "agenteval-reports"
default_max_cost_usd = 1.0
default_max_latency_ms = 30000
```

### Environment Variables

All settings can be set via `AGENTEVAL_` prefixed environment variables:

```bash
export AGENTEVAL_EVAL_PROVIDER=bedrock
export AGENTEVAL_EVAL_MODEL=anthropic.claude-3-haiku-20240307-v1:0
export AGENTEVAL_AWS_PROFILE=my-aws-profile
export AGENTEVAL_AWS_REGION=us-west-2
export AGENTEVAL_OPENAI_BASE_URL=http://localhost:8080/v1
export AGENTEVAL_OPENAI_API_KEY=sk-custom

pytest tests/agent_evals/ -v
```

### Eval model setup by provider

**Ollama (free, local) — recommended for getting started**
```bash
ollama pull llama3.2
pip install agenteval-ai[all]
# No config needed — auto-detected as default eval model
```

**OpenAI**
```toml
[tool.agenteval]
eval_provider = "openai"
eval_model = "gpt-4o-mini"
openai_api_key = "sk-..."
```

**OpenAI-compatible APIs** (vLLM, LiteLLM, Together AI, local servers)
```toml
[tool.agenteval]
eval_provider = "openai"
eval_model = "my-custom-model"
openai_base_url = "http://localhost:8080/v1"
openai_api_key = "sk-custom"     # optional, depends on your server
```

**AWS Bedrock**
```bash
pip install agenteval-ai[bedrock]
```

```toml
[tool.agenteval]
eval_provider = "bedrock"
eval_model = "anthropic.claude-3-haiku-20240307-v1:0"
aws_profile = "my-profile"    # optional, uses default credential chain if omitted
aws_region = "us-east-1"      # optional, uses boto3 default if omitted
```

## MCP Server

Works with all major AI coding tools:

```bash
agenteval mcp install                        # auto-configures all detected tools
agenteval mcp install --platform claude-code # Claude Code only
agenteval mcp install --platform copilot     # VS Code / GitHub Copilot
agenteval mcp install --platform cursor      # Cursor
agenteval mcp install --platform windsurf    # Windsurf
agenteval mcp serve                          # start the server (stdio)
```

| Tool | Config Path |
|---|---|
| Claude Code | `~/.claude/settings.json` |
| VS Code / Copilot | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |

8 tools: `run_eval`, `run_single_test`, `check_regression`, `show_cost_report`, `list_evaluators`, `generate_test`, `save_baseline`, `explain_failure`

## AI Coding Tool Skills

```bash
agenteval skill install --platform all
```

Installs skills for Claude Code, GitHub Copilot, Cursor, and Windsurf. After installation, your AI coding tool can:

- Test agents with `/eval-agent`
- Generate test files with `/generate-tests`
- Check regressions with `/check-regression`
- Audit costs with `/cost-audit`
- Audit security with `/security-audit`

## GitHub Action

Add agent testing to your CI in 5 lines:

```yaml
# .github/workflows/agenteval.yml
name: Agent Tests
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: devbrat-anand/agenteval@v1
        with:
          fail_under: "0.8"
```

Posts a results table as a PR comment with scores, costs, and pass/fail status.

## Comparison

| Feature | agenteval | DeepEval | TruLens | RAGAS | LangSmith |
|---|---|---|---|---|---|
| Multi-step agent trajectories | ✅ | Partial | ❌ | ❌ | ✅ |
| Framework-agnostic | ✅ | ✅ | ❌ | ❌ | ❌ |
| Protocol-level interception | ✅ | ❌ | ❌ | ❌ | ❌ |
| pytest native | ✅ | ✅ | ❌ | ❌ | ❌ |
| $0 local evals (Ollama) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Multi-provider (4 SDKs) | ✅ | ❌ | ❌ | ❌ | ❌ |
| MCP server | ✅ | ❌ | ❌ | ❌ | ❌ |
| GitHub Action with PR bot | ✅ | ❌ | ❌ | ❌ | ❌ |
| AI coding tool skills | ✅ | ❌ | ❌ | ❌ | ❌ |
| Open source (MIT) | ✅ | ✅ | ✅ | ✅ | ❌ |

## Examples

| Example | Provider | What It Tests |
|---|---|---|
| [quickstart](examples/quickstart/) | None (echo) | Basic structure |
| [openai_agent](examples/openai_agent/) | OpenAI | Tool-calling agent: cost, convergence, security, hallucination, scope |
| [bedrock_agent](examples/bedrock_agent/) | AWS Bedrock | Tool-calling agent (Converse API): cost, security, hallucination, scope |
| [langchain_agent](examples/langchain_agent/) | OpenAI + LangChain | Tool calls, hallucination, scope |
| [ollama_local](examples/ollama_local/) | Ollama | $0 local evals: security, convergence, hallucination, scope |

## Custom Evaluators

Write your own evaluator and share it as a Python package:

```python
from agenteval.evaluators.base import Evaluator
from agenteval.core.models import Trace, EvalResult

class ToxicityEvaluator(Evaluator):
    name = "toxicity"

    def evaluate(self, trace: Trace, criteria: dict) -> EvalResult:
        # Your logic here
        ...
```

Register via entry points:

```toml
[project.entry-points."agenteval.evaluators"]
toxicity = "my_package:ToxicityEvaluator"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:

- New evaluators
- New provider interceptors
- Bug fixes and documentation improvements
- Example projects

## License

MIT — see [LICENSE](LICENSE) for details.
