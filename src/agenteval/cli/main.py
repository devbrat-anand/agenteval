"""agenteval CLI entry point."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from agenteval import __version__


@click.group()
def cli() -> None:
    """agenteval — pytest for AI agents. Catch failures before production."""


@cli.command()
def version() -> None:
    """Show agenteval version."""
    click.echo(f"agenteval {__version__}")


@cli.command()
@click.argument("test_path", default="tests/")
@click.option(
    "--fail-under", type=float, default=None, help="Fail if avg score below threshold (0.0-1.0)"
)
@click.option(
    "--max-cost", type=float, default=None, help="Fail if total cost exceeds budget (USD)"
)
@click.option("--report", type=str, default=None, help="Report format: console, html, json")
@click.option("--report-dir", type=str, default="agenteval-reports", help="Report output directory")
@click.option(
    "--baseline", type=str, default=None, help="Baseline directory for regression comparison"
)
@click.option("--regression-threshold", type=float, default=0.05, help="Max allowed score drop")
@click.option(
    "--save-baseline", type=str, default=None, help="Save results as baseline to this directory"
)
def run(
    test_path,
    fail_under,
    max_cost,
    report,
    report_dir,
    baseline,
    regression_threshold,
    save_baseline,
) -> None:
    """Run agent evaluation tests."""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    if fail_under is not None:
        cmd.extend(["--agenteval-fail-under", str(fail_under)])
    if max_cost is not None:
        cmd.extend(["--agenteval-max-cost", str(max_cost)])
    if report is not None:
        cmd.extend(["--agenteval-report", report])
    if save_baseline is not None:
        cmd.extend(["--agenteval-report", "json", "--agenteval-report-dir", save_baseline])
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@cli.command()
def init() -> None:
    """Initialize agenteval in your project — detect setup and scaffold tests."""
    from agenteval.cli.scaffold import detect_project, scaffold

    project_dir = Path.cwd()
    detection = detect_project(project_dir)

    if detection["providers"]:
        click.echo(f"Detected providers: {', '.join(detection['providers'])}")
    if detection["frameworks"]:
        click.echo(f"Detected frameworks: {', '.join(detection['frameworks'])}")

    created = scaffold(project_dir)
    if created:
        for _name, path in created.items():
            click.echo(f"  Created: {path}")
        click.echo("\nRun your first eval:")
        click.echo("  pytest tests/agent_evals/ -v")
    else:
        click.echo("Tests already exist. Nothing to scaffold.")


@cli.command("show-pricing")
def show_pricing() -> None:
    """Show bundled model pricing data."""
    from agenteval.interceptors.pricing import PricingEngine

    engine = PricingEngine()
    click.echo(f"Pricing data loaded: {len(engine._table)} providers")
    for provider in engine.available_providers():
        click.echo(f"  - {provider}")


@cli.group()
def mcp() -> None:
    """MCP server commands."""


@mcp.command()
def serve() -> None:
    """Start the agenteval MCP server."""
    try:
        import asyncio

        from mcp.server.stdio import stdio_server

        from agenteval.mcp.server import create_server

        server = create_server()

        async def run() -> None:
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())

        asyncio.run(run())
    except ImportError:
        click.echo("MCP not installed. Run: pip install agenteval[mcp]", err=True)
        sys.exit(1)


@mcp.command()
@click.option(
    "--platform",
    type=click.Choice(["claude-code", "copilot", "cursor", "windsurf", "all"]),
    default="all",
    help="Target platform (default: all detected)",
)
def install(platform: str) -> None:
    """Auto-configure agenteval MCP server in AI coding tools."""
    from agenteval.mcp.installer import install_mcp

    results = install_mcp(platform=platform)
    if results:
        for path in results:
            click.echo(f"  Configured: {path}")
        click.echo(f"MCP server installed for {len(results)} tool(s)")
    else:
        import json as json_mod

        from agenteval.mcp.installer import resolve_server_entry

        click.echo("No AI coding tool configs found. Manual setup:")
        click.echo(
            json_mod.dumps(
                {
                    "mcpServers": {"agenteval": resolve_server_entry()},
                },
                indent=2,
            )
        )


@cli.group()
def skill() -> None:
    """AI coding tool skill commands."""


@skill.command("install")
@click.option(
    "--platform",
    type=str,
    default=None,
    help="Target platform: claude-code, copilot, cursor, windsurf, all",
)
def skill_install(platform: str | None) -> None:
    """Install agenteval skills for AI coding tools."""
    from agenteval.skill.installer import install_skills

    results = install_skills(Path.cwd(), platform=platform)
    if results:
        for plat, files in results.items():
            click.echo(f"  {plat}: {len(files)} files installed")
        click.echo(f"Installed skills for: {', '.join(results.keys())}")
    else:
        click.echo("No platforms detected. Use --platform to specify.")


if __name__ == "__main__":
    cli()
