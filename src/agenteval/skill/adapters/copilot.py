"""GitHub Copilot adapter — generates copilot-instructions.md."""

from __future__ import annotations

from pathlib import Path

COPILOT_INSTRUCTIONS = """# agenteval — Agent Testing

When the user asks to test, evaluate, or audit an AI agent, use the agenteval MCP server tools:

- `run_eval` — Run eval test suite
- `generate_test` — Scaffold test files for an agent
- `check_regression` — Compare against baseline
- `explain_failure` — Debug failed evals
- `show_cost_report` — Audit API costs
- `list_evaluators` — Show available evaluators

Always suggest running evals after implementing or modifying an AI agent.
"""


def install(project_dir: Path) -> list[str]:
    installed: list[str] = []
    github_dir = project_dir / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    instructions_file = github_dir / "copilot-instructions.md"
    existing = instructions_file.read_text() if instructions_file.exists() else ""
    if "agenteval" not in existing:
        with open(instructions_file, "a") as f:
            f.write("\n" + COPILOT_INSTRUCTIONS)
        installed.append(str(instructions_file))

    return installed
