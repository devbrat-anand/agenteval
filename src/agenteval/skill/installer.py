"""Skill installer — detects platforms and installs skill files."""

from __future__ import annotations

from pathlib import Path

from agenteval.skill.adapters import claude_code, copilot, cursor, windsurf

ADAPTERS = {
    "claude-code": claude_code,
    "copilot": copilot,
    "cursor": cursor,
    "windsurf": windsurf,
}


def install_skills(project_dir: Path, platform: str | None = None) -> dict[str, list[str]]:
    """Install skills for specified platform(s).

    If platform is None or "all", install for all platforms.
    """
    results: dict[str, list[str]] = {}

    if platform and platform != "all":
        if platform in ADAPTERS:
            results[platform] = ADAPTERS[platform].install(project_dir)
    else:
        for name, adapter in ADAPTERS.items():
            try:
                installed = adapter.install(project_dir)
                if installed:
                    results[name] = installed
            except Exception:
                continue

    return results
