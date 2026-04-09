"""Cursor adapter — generates .cursorrules."""

from __future__ import annotations

from pathlib import Path

CURSOR_RULES = """
# agenteval — Agent Testing
When working with AI agents, use agenteval MCP tools to test and evaluate them.
Available tools: run_eval, generate_test, check_regression,
explain_failure, show_cost_report, list_evaluators.
After modifying agent code, suggest running `agenteval run tests/agent_evals/` to verify.
"""


def install(project_dir: Path) -> list[str]:
    installed: list[str] = []
    rules_file = project_dir / ".cursorrules"
    existing = rules_file.read_text() if rules_file.exists() else ""
    if "agenteval" not in existing:
        with open(rules_file, "a") as f:
            f.write("\n" + CURSOR_RULES)
        installed.append(str(rules_file))
    return installed
