from pathlib import Path

from agenteval.skill.installer import install_skills


def test_install_claude_code(tmp_path: Path):
    results = install_skills(tmp_path, platform="claude-code")
    assert "claude-code" in results
    assert len(results["claude-code"]) > 0
    skills_dir = tmp_path / ".claude" / "skills"
    assert skills_dir.exists()


def test_install_copilot(tmp_path: Path):
    results = install_skills(tmp_path, platform="copilot")
    assert "copilot" in results
    instructions = tmp_path / ".github" / "copilot-instructions.md"
    assert instructions.exists()
    assert "agenteval" in instructions.read_text()


def test_install_cursor(tmp_path: Path):
    results = install_skills(tmp_path, platform="cursor")
    assert "cursor" in results
    assert (tmp_path / ".cursorrules").exists()


def test_install_windsurf(tmp_path: Path):
    results = install_skills(tmp_path, platform="windsurf")
    assert "windsurf" in results
    assert (tmp_path / ".windsurfrules").exists()


def test_install_all(tmp_path: Path):
    results = install_skills(tmp_path, platform="all")
    assert len(results) == 4
