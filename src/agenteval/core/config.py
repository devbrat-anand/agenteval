"""Configuration loading for agenteval."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AgentEvalConfig(BaseModel):
    eval_provider: str = "ollama"
    eval_model: str = "llama3.2"
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    aws_profile: str | None = None
    aws_region: str | None = None
    default_max_cost_usd: float = 1.0
    default_max_latency_ms: int = 30000
    interceptors: list[str] | None = None
    report_format: str = "console"
    report_dir: str = "agenteval-reports"
    baseline_dir: str = "tests/baselines"
    regression_threshold: float = 0.05


def _read_pyproject_toml(project_dir: Path) -> dict[str, Any]:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        return {}
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[import-not-found]

    with open(pyproject_path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)
    tool_section = data.get("tool", {})
    if not isinstance(tool_section, dict):
        return {}
    agenteval_section = tool_section.get("agenteval", {})
    if not isinstance(agenteval_section, dict):
        return {}
    return agenteval_section


_LIST_FIELDS = {"interceptors"}


def _read_env_vars() -> dict[str, Any]:
    prefix = "AGENTEVAL_"
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix) :].lower()
            if config_key in _LIST_FIELDS:
                result[config_key] = [v.strip() for v in value.split(",") if v.strip()]
            else:
                result[config_key] = value
    return result


def load_config(project_dir: Path | None = None) -> AgentEvalConfig:
    if project_dir is None:
        project_dir = Path.cwd()

    file_config = _read_pyproject_toml(project_dir)
    env_config = _read_env_vars()

    merged = {**file_config, **env_config}
    return AgentEvalConfig(**merged)
