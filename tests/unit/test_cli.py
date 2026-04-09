from click.testing import CliRunner

from agenteval.cli.main import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "agenteval" in result.output
    assert "run" in result.output
    assert "version" in result.output
    assert "show-pricing" in result.output


def test_cli_run_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "--fail-under" in result.output
    assert "--max-cost" in result.output
    assert "--report" in result.output
    assert "--report-dir" in result.output
    assert "--save-baseline" in result.output


def test_cli_run_nonexistent_path():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "nonexistent_path/"])
    assert result.exit_code != 0
