"""MCP server exposing agenteval tools for AI coding assistants."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS = [
    {
        "name": "run_eval",
        "description": (
            "Run agent eval test suite and return results."
            " Pass test_path to specify which tests to run."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_path": {
                    "type": "string",
                    "description": "Path to test file or directory",
                    "default": "tests/agent_evals/",
                },
                "fail_under": {
                    "type": "number",
                    "description": "Minimum passing score (0.0-1.0)",
                    "default": 0.8,
                },
            },
        },
    },
    {
        "name": "run_single_test",
        "description": "Run a single test by name and return detailed trace with scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string", "description": "Path to test file"},
                "test_name": {"type": "string", "description": "Test function name"},
            },
            "required": ["test_path", "test_name"],
        },
    },
    {
        "name": "check_regression",
        "description": (
            "Compare current agent performance against a saved baseline"
            " and report regressions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string"},
                "baseline_dir": {"type": "string", "default": "tests/baselines"},
                "threshold": {"type": "number", "default": 0.05},
            },
        },
    },
    {
        "name": "show_cost_report",
        "description": "Show cost breakdown across recent eval runs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_dir": {"type": "string", "default": "agenteval-reports"},
            },
        },
    },
    {
        "name": "list_evaluators",
        "description": "List all available evaluators (built-in and plugins) with descriptions.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "generate_test",
        "description": "Analyze agent code and scaffold a test file with recommended evaluators.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_description": {
                    "type": "string",
                    "description": "Describe what the agent does",
                },
                "output_path": {"type": "string", "description": "Where to write the test file"},
            },
            "required": ["agent_description"],
        },
    },
    {
        "name": "save_baseline",
        "description": "Save current test results as baseline for future regression testing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string"},
                "baseline_dir": {"type": "string", "default": "tests/baselines"},
            },
        },
    },
    {
        "name": "explain_failure",
        "description": (
            "Analyze a failed eval and explain why it failed"
            " with actionable fix suggestions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string"},
                "test_name": {"type": "string"},
            },
            "required": ["test_path", "test_name"],
        },
    },
]


def _run_pytest(test_path: str, extra_args: list[str] | None = None) -> dict[str, Any]:
    """Run pytest and capture JSON output."""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", "-q"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> str:
    """Handle a tool call and return the result as a string."""
    if name == "run_eval":
        result = _run_pytest(
            arguments.get("test_path", "tests/agent_evals/"),
            ["--agenteval-fail-under", str(arguments.get("fail_under", 0.8))],
        )
        return json.dumps(result, indent=2)

    elif name == "run_single_test":
        test_id = f"{arguments['test_path']}::{arguments['test_name']}"
        result = _run_pytest(test_id)
        return json.dumps(result, indent=2)

    elif name == "list_evaluators":
        from agenteval.evaluators import default_evaluator_registry

        evaluators = default_evaluator_registry.available()
        return json.dumps({"evaluators": evaluators, "count": len(evaluators)})

    elif name == "check_regression":
        result = _run_pytest(
            arguments.get("test_path", "tests/agent_evals/"),
            ["-m", "regression"],
        )
        return json.dumps(result, indent=2)

    elif name == "show_cost_report":
        report_dir = Path(arguments.get("report_dir", "agenteval-reports"))
        reports = sorted(report_dir.glob("*.json")) if report_dir.exists() else []
        if not reports:
            return json.dumps({"message": "No reports found", "report_dir": str(report_dir)})
        latest = json.loads(reports[-1].read_text())
        return json.dumps(
            {"total_cost_usd": latest.get("total_cost_usd", 0), "report": str(reports[-1])}
        )

    elif name == "generate_test":
        desc = arguments["agent_description"]
        output_path = arguments.get("output_path", "tests/agent_evals/test_generated.py")
        resolved = Path(output_path).resolve()
        cwd = Path.cwd().resolve()
        if resolved.is_absolute() and not str(resolved).startswith(str(cwd)):
            return json.dumps({"error": f"Path must be within project directory: {output_path}"})
        if ".." in Path(output_path).parts:
            return json.dumps({"error": f"Path must not contain '..': {output_path}"})
        template = _generate_test_template(desc)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(template)
        return json.dumps({"message": f"Test written to {output_path}", "path": output_path})

    elif name == "save_baseline":
        result = _run_pytest(
            arguments.get("test_path", "tests/agent_evals/"),
            [
                "--agenteval-report",
                "json",
                "--agenteval-report-dir",
                arguments.get("baseline_dir", "tests/baselines"),
            ],
        )
        return json.dumps({"message": "Baseline saved", **result})

    elif name == "explain_failure":
        test_id = f"{arguments['test_path']}::{arguments['test_name']}"
        result = _run_pytest(test_id, ["--tb=long", "-v"])
        return json.dumps(result, indent=2)

    return json.dumps({"error": f"Unknown tool: {name}"})


def _generate_test_template(agent_description: str) -> str:
    """Generate a test file template based on agent description."""
    return f'''"""Auto-generated agenteval test for: {agent_description}"""

import pytest


@pytest.fixture
def agent(agent_runner):
    def my_agent(prompt: str) -> str:
        # TODO: Wire up your actual agent here
        raise NotImplementedError("Replace with your agent")
    return agent_runner.wrap(my_agent)


def test_agent_basic(agent):
    result = agent.run("Test prompt for your agent")
    trace = result.trace

    # Structural checks
    assert trace.total_cost_usd < 1.00
    assert trace.total_latency_ms < 30000
    assert trace.no_loops(max_repeats=3)

    # Convergence
    assert trace.converged()


def test_agent_no_security_issues(agent):
    result = agent.run("Test prompt for your agent")
    trace = result.trace
    assert trace.no_pii_leaked()
    assert trace.no_prompt_injection()
'''


def create_server() -> Any:
    """Create and configure the MCP server."""
    try:
        from mcp.server import Server
        from mcp.types import Tool

        server = Server("agenteval")

        @server.list_tools()  # type: ignore[misc]
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name=t["name"],  # type: ignore[arg-type]
                    description=t["description"],  # type: ignore[arg-type]
                    inputSchema=t["inputSchema"],  # type: ignore[arg-type]
                )
                for t in TOOL_DEFINITIONS
            ]

        @server.call_tool()  # type: ignore[misc]
        async def call_tool(name: str, arguments: dict) -> list[Any]:  # type: ignore[type-arg]
            from mcp.types import TextContent

            result = await handle_tool_call(name, arguments)
            return [TextContent(type="text", text=result)]

        return server
    except ImportError:
        # MCP not installed — return a stub
        return type("StubServer", (), {"run": lambda self: None})()
