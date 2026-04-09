# CLI Reference

Complete reference for the `agenteval` command-line interface.

## Overview

The `agenteval` CLI provides commands for running evals, scaffolding tests, managing MCP servers, and installing skills.

```bash
agenteval [COMMAND] [OPTIONS]
```

## Commands

### `run`

Run agent evaluations.

```bash
agenteval run [TEST_PATH] [OPTIONS]
```

**Arguments:**
- `TEST_PATH`: Path to test file/directory (default: `tests/agent_evals/`)

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-v, --verbose` | Verbose output | `False` |
| `-q, --quiet` | Minimal output | `False` |
| `-n, --parallel N` | Run N tests in parallel (`auto` = auto-detect CPUs) | `1` |
| `--fail-under SCORE` | Fail if overall score < SCORE (0.0-1.0) | `None` |
| `--fail-under-cost COST` | Fail if any test cost > COST (USD) | `None` |
| `--fail-under-latency MS` | Fail if any test latency > MS (milliseconds) | `None` |
| `--max-total-cost COST` | Abort if total cost exceeds COST (USD) | `None` |
| `--baseline FILE` | Compare against baseline (JSON file) | `None` |
| `--save-baseline FILE` | Save results as baseline | `None` |
| `--fail-on-regression` | Fail if metrics regress vs. baseline | `False` |
| `--report FORMAT` | Generate report (`html`, `json`, `junit`) | `None` |
| `--report-dir DIR` | Output directory for reports | `reports/` |
| `--rate-limit N` | Max N API requests per second | `None` |
| `-k EXPRESSION` | Only run tests matching EXPRESSION | `None` |
| `-m MARKER` | Only run tests with MARKER | `None` |
| `--provider PROVIDER` | Force provider (`openai`, `bedrock`, etc.) | Auto-detect |
| `--eval-provider PROVIDER` | Provider for LLM-judge evals | Auto-detect |
| `--eval-model MODEL` | Model for LLM-judge evals | Auto-detect |

**Examples:**

```bash
# Basic run
agenteval run tests/agent_evals/ -v

# With score threshold
agenteval run --fail-under 0.8

# With cost and latency limits
agenteval run --fail-under-cost 0.50 --fail-under-latency 10000

# Generate HTML report
agenteval run --report html --report-dir reports/

# Compare against baseline
agenteval run --baseline baseline.json --fail-on-regression

# Parallel execution
agenteval run -n auto

# Run specific tests
agenteval run -k "test_agent_cost" -v

# Run tests with marker
agenteval run -m agenteval -v

# Use Ollama for $0 evals
agenteval run --eval-provider ollama --eval-model llama3.2
```

**Exit Codes:**
- `0`: All tests passed
- `1`: Some tests failed
- `2`: Regression detected (with `--fail-on-regression`)
- `3`: Cost limit exceeded
- `4`: Score below threshold

---

### `init`

Scaffold agent eval tests for your project.

```bash
agenteval init [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--path DIR` | Output directory | `tests/agent_evals/` |
| `--provider PROVIDER` | Provider to scaffold for | Auto-detect |
| `--force` | Overwrite existing files | `False` |
| `--template TEMPLATE` | Use specific template | `default` |

**What it creates:**

1. `conftest.py` — Fixtures wired to your agent
2. `test_example.py` — Example tests for your agent type
3. `.agenteval.yml` — Configuration file

**Detection Logic:**

Auto-detects based on installed packages:

| Installed | Generated Template |
|-----------|-------------------|
| `openai` | OpenAI agent example |
| `boto3` | AWS Bedrock example |
| `anthropic` | Anthropic example |
| `langchain` | LangChain example |
| `ollama` | Ollama example |

**Examples:**

```bash
# Auto-detect and scaffold
agenteval init

# Scaffold for specific provider
agenteval init --provider openai

# Custom output path
agenteval init --path tests/my_evals/

# Force overwrite existing files
agenteval init --force
```

---

### `version`

Print agenteval version.

```bash
agenteval version
```

**Output:**
```
agenteval version 0.1.0
Python 3.12.0
Platform: darwin (macOS)
```

---

### `mcp serve`

Start the agenteval MCP server for use with Claude Code, Cursor, Windsurf, etc.

```bash
agenteval mcp serve [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--host HOST` | Host to bind | `localhost` |
| `--port PORT` | Port to bind | `3000` |
| `--stdio` | Use stdio transport (for Claude Code) | `False` |

**Examples:**

```bash
# Start MCP server (stdio mode for Claude Code)
agenteval mcp serve --stdio

# Start HTTP server
agenteval mcp serve --host 0.0.0.0 --port 3000
```

**MCP Tools Provided:**

1. `run_agent_evals` — Run agent tests
2. `get_eval_results` — Get test results
3. `scaffold_tests` — Generate test files
4. `get_agent_trace` — Get execution trace for a test

**Usage in Claude Code:**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agenteval": {
      "command": "agenteval",
      "args": ["mcp", "serve", "--stdio"]
    }
  }
}
```

---

### `mcp install`

Install agenteval as an MCP server (helper command).

```bash
agenteval mcp install [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--client CLIENT` | Client to install for (`claude`, `cursor`, `windsurf`) | `claude` |

**What it does:**

1. Detects client config location
2. Adds agenteval MCP server to config
3. Validates config

**Examples:**

```bash
# Install for Claude Code
agenteval mcp install --client claude

# Install for Cursor
agenteval mcp install --client cursor
```

---

### `skill install`

Install agenteval skill for Claude Code, Copilot, etc.

```bash
agenteval skill install [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--client CLIENT` | Client to install for (`claude`, `copilot`, `cursor`, `windsurf`) | `claude` |

**What it does:**

1. Detects client skills directory
2. Installs `agenteval.md` skill
3. Validates skill

**Usage:**

```bash
# Install for Claude Code
agenteval skill install --client claude

# Install for Copilot
agenteval skill install --client copilot
```

Then in your client:

```
/agenteval run tests/agent_evals/
```

---

### `evaluators list`

List all available evaluators (built-in + plugins).

```bash
agenteval evaluators list
```

**Output:**

```
Built-in Evaluators (13):

Structural (5):
  - no_loops: Detect infinite loops
  - converged: Check clean termination
  - tool_called: Check if tool was called
  - tool_not_called: Check if tool NOT called
  - tool_call_order: Check tool call sequence

Semantic (3):
  - semantic_similarity: Compare output to expected
  - hallucination_score: Detect hallucinations
  - output_quality: Evaluate output quality

Safety (3):
  - no_pii_leaked: Detect PII leakage
  - no_prompt_injection: Detect prompt injection
  - content_safety: Detect unsafe content

Operational (2):
  - total_cost_usd: Track execution cost
  - total_latency_ms: Track execution latency

Plugin Evaluators (0):
  (none installed)
```

---

### `interceptors list`

List all available interceptors.

```bash
agenteval interceptors list
```

**Output:**

```
Built-in Interceptors (4):

  - openai: OpenAI API (openai>=1.0.0)
  - bedrock: AWS Bedrock (boto3>=1.28.0)
  - anthropic: Anthropic API (anthropic>=0.18.0)
  - ollama: Ollama (ollama>=0.1.0)

Plugin Interceptors (0):
  (none installed)
```

---

### `pricing list`

List model pricing.

```bash
agenteval pricing list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--provider PROVIDER` | Filter by provider | `None` |
| `--format FORMAT` | Output format (`table`, `json`, `csv`) | `table` |

**Examples:**

```bash
# List all pricing
agenteval pricing list

# Only OpenAI
agenteval pricing list --provider openai

# JSON output
agenteval pricing list --format json
```

---

### `pricing update`

Update pricing database from providers.

```bash
agenteval pricing update
```

Fetches latest pricing from:
- OpenAI pricing page
- AWS Bedrock pricing API
- Anthropic pricing page

---

### `config show`

Show current configuration.

```bash
agenteval config show
```

**Output:**

```yaml
# agenteval configuration

# Test paths
test_path: tests/agent_evals/

# Providers
provider: auto  # Auto-detected
eval_provider: ollama
eval_model: llama3.2

# Thresholds
fail_under: 0.8
fail_under_cost: null
fail_under_latency: null
max_total_cost: null

# Reporting
report_formats: [html, json]
report_dir: reports/

# Parallelization
parallel: 1
rate_limit: null

# Regression testing
baseline: baseline.json
fail_on_regression: true
```

---

### `config set`

Set configuration value.

```bash
agenteval config set KEY VALUE
```

**Examples:**

```bash
agenteval config set fail_under 0.8
agenteval config set eval_provider ollama
agenteval config set parallel auto
```

---

### `config reset`

Reset configuration to defaults.

```bash
agenteval config reset
```

---

## Environment Variables

Override config via environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENTEVAL_PROVIDER` | Force agent provider | `openai` |
| `AGENTEVAL_EVAL_PROVIDER` | Force eval provider | `ollama` |
| `AGENTEVAL_EVAL_MODEL` | Force eval model | `llama3.2` |
| `AGENTEVAL_FAIL_UNDER` | Minimum score threshold | `0.8` |
| `AGENTEVAL_MAX_TOTAL_COST` | Max total cost (USD) | `5.00` |
| `AGENTEVAL_DISABLE_OPENAI` | Disable OpenAI interceptor | `1` |
| `AGENTEVAL_DISABLE_BEDROCK` | Disable Bedrock interceptor | `1` |
| `AGENTEVAL_CUSTOM_PRICING` | Custom model pricing (JSON) | `{"my-model": {...}}` |

**Example:**

```bash
export AGENTEVAL_EVAL_PROVIDER=ollama
export AGENTEVAL_EVAL_MODEL=llama3.2
export AGENTEVAL_FAIL_UNDER=0.8

agenteval run tests/agent_evals/ -v
```

---

## Configuration File

Use `.agenteval.yml` for persistent config:

```yaml
# .agenteval.yml

# Test configuration
test_path: tests/agent_evals/
parallel: auto

# Provider configuration
provider: auto
eval_provider: ollama
eval_model: llama3.2

# Thresholds
fail_under: 0.8
fail_under_cost: 0.50
fail_under_latency: 10000
max_total_cost: 5.00

# Baseline regression testing
baseline: baseline.json
fail_on_regression: true

# Reporting
report_formats:
  - html
  - json
report_dir: reports/

# Rate limiting
rate_limit: 10  # Max 10 req/sec
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Test failures |
| `2` | Regression detected |
| `3` | Cost limit exceeded |
| `4` | Score below threshold |
| `5` | Configuration error |
| `6` | Provider not detected |

---

## Examples

### Full CI Pipeline

```bash
#!/bin/bash
set -e

# Install dependencies
pip install agenteval[all]

# Run evals with all checks
agenteval run tests/agent_evals/ \
  --baseline baseline.json \
  --fail-on-regression \
  --fail-under 0.8 \
  --fail-under-cost 0.50 \
  --fail-under-latency 10000 \
  --max-total-cost 5.00 \
  --report html \
  --report json \
  --report junit \
  --report-dir reports/ \
  -n auto \
  -v

# Upload reports
aws s3 cp reports/ s3://my-bucket/reports/ --recursive
```

### Local Development

```bash
# Quick run
agenteval run -v

# With Ollama for $0 evals
agenteval run --eval-provider ollama --eval-model llama3.2

# Specific test
agenteval run -k "test_agent_cost" -v

# Save as baseline
agenteval run --save-baseline baseline.json
```

### Debugging

```bash
# Verbose output
agenteval run -vv

# Single test, no parallel
agenteval run -k "test_specific" -n 1 -vv

# Show trace
agenteval run -k "test_specific" --show-trace
```

---

## Next Steps

- [Quickstart](../quickstart.md) — Get started with agenteval
- [CI/CD Integration](../guides/ci-cd.md) — Use CLI in CI pipelines
- [Provider Setup](../guides/providers.md) — Configure providers
