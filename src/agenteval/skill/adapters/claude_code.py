"""Claude Code skill adapter — generates CLAUDE.md and skill files."""

from __future__ import annotations

from pathlib import Path


def install(project_dir: Path) -> list[str]:
    """Install agenteval skills for Claude Code."""
    installed: list[str] = []

    skills_dir = project_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    core_dir = Path(__file__).parent.parent / "core"
    for skill_file in core_dir.glob("*.md"):
        dest = skills_dir / f"agenteval-{skill_file.name}"
        dest.write_text(skill_file.read_text())
        installed.append(str(dest))

    return installed
