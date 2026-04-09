"""Console reporter using rich for colored terminal output."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from agenteval.core.models import SuiteResult
from agenteval.reporting.base import Reporter


class ConsoleReporter(Reporter):
    def render(self, suite: SuiteResult, output_path: Path | None = None) -> None:
        console = Console()
        console.print()
        console.rule("[bold]agenteval results[/bold]")
        console.print()

        table = Table(show_header=True)
        table.add_column("Test", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Status", justify="center")

        for test in suite.tests:
            status = "[green]PASS[/green]" if test.passed else "[red]FAIL[/red]"
            table.add_row(
                test.test_name,
                f"{test.overall_score:.2f}",
                f"${test.trace.total_cost_usd:.6f}",
                f"{test.duration_ms:.0f}ms",
                status,
            )

            if not test.passed:
                for er in test.eval_results:
                    if not er.passed:
                        table.add_row(
                            f"  [dim]└─ {er.evaluator}[/dim]",
                            f"[dim]{er.score:.2f}[/dim]",
                            "",
                            "",
                            f"[dim red]{er.reason}[/dim red]",
                        )

        console.print(table)
        console.print()
        console.print(
            f"[bold]{suite.total_passed} passed[/bold], "
            f"[bold red]{suite.total_failed} failed[/bold red] | "
            f"avg score: {suite.avg_score:.2f} | "
            f"total: ${suite.total_cost_usd:.6f} | "
            f"{suite.total_duration_ms:.0f}ms"
        )
        console.print()
