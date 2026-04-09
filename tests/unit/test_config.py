from pathlib import Path

from agenteval.core.config import AgentEvalConfig, load_config


def test_default_config():
    config = AgentEvalConfig()
    assert config.eval_provider == "ollama"
    assert config.eval_model == "llama3.2"
    assert config.default_max_cost_usd == 1.0
    assert config.default_max_latency_ms == 30000
    assert config.report_format == "console"
    assert config.report_dir == "agenteval-reports"
    assert config.baseline_dir == "tests/baselines"
    assert config.regression_threshold == 0.05
    assert config.interceptors is None


def test_config_from_dict():
    config = AgentEvalConfig(
        eval_provider="openai",
        eval_model="gpt-4o-mini",
        default_max_cost_usd=5.0,
    )
    assert config.eval_provider == "openai"
    assert config.eval_model == "gpt-4o-mini"
    assert config.default_max_cost_usd == 5.0


def test_load_config_returns_defaults_when_no_file(tmp_path: Path):
    config = load_config(project_dir=tmp_path)
    assert config.eval_provider == "ollama"


def test_load_config_reads_pyproject_toml(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.agenteval]\n"
        'eval_provider = "openai"\n'
        'eval_model = "gpt-4o-mini"\n'
        "default_max_cost_usd = 2.5\n"
    )
    config = load_config(project_dir=tmp_path)
    assert config.eval_provider == "openai"
    assert config.eval_model == "gpt-4o-mini"
    assert config.default_max_cost_usd == 2.5


def test_env_vars_override_config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AGENTEVAL_EVAL_PROVIDER", "openai")
    monkeypatch.setenv("AGENTEVAL_EVAL_MODEL", "gpt-4o")
    config = load_config(project_dir=tmp_path)
    assert config.eval_provider == "openai"
    assert config.eval_model == "gpt-4o"


def test_default_config_openai_fields():
    config = AgentEvalConfig()
    assert config.openai_base_url is None
    assert config.openai_api_key is None


def test_default_config_aws_fields():
    config = AgentEvalConfig()
    assert config.aws_profile is None
    assert config.aws_region is None


def test_openai_base_url_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AGENTEVAL_OPENAI_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("AGENTEVAL_OPENAI_API_KEY", "sk-custom")
    config = load_config(project_dir=tmp_path)
    assert config.openai_base_url == "http://localhost:8080/v1"
    assert config.openai_api_key == "sk-custom"


def test_aws_profile_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AGENTEVAL_AWS_PROFILE", "my-profile")
    monkeypatch.setenv("AGENTEVAL_AWS_REGION", "us-west-2")
    config = load_config(project_dir=tmp_path)
    assert config.aws_profile == "my-profile"
    assert config.aws_region == "us-west-2"
