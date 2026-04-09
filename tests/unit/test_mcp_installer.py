import json
from pathlib import Path

from agenteval.mcp.installer import install_mcp


def test_install_claude_code(tmp_path, monkeypatch):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    results = install_mcp(platform="claude-code")
    assert len(results) == 1

    config = json.loads((claude_dir / "settings.json").read_text())
    assert "agenteval" in config["mcpServers"]
    assert "command" in config["mcpServers"]["agenteval"]
    assert config["mcpServers"]["agenteval"]["args"][-2:] == ["mcp", "serve"]


def test_install_copilot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vscode").mkdir()

    results = install_mcp(platform="copilot")
    assert len(results) == 1

    config = json.loads((tmp_path / ".vscode" / "mcp.json").read_text())
    assert "agenteval" in config["servers"]
    assert config["servers"]["agenteval"]["type"] == "stdio"


def test_install_copilot_skips_when_no_vscode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = install_mcp(platform="copilot")
    assert len(results) == 0


def test_install_cursor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".cursor").mkdir()

    results = install_mcp(platform="cursor")
    assert len(results) == 1

    config = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    assert "agenteval" in config["mcpServers"]
    assert config["mcpServers"]["agenteval"]["args"][-2:] == ["mcp", "serve"]


def test_install_cursor_skips_when_no_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = install_mcp(platform="cursor")
    assert len(results) == 0


def test_install_windsurf(tmp_path, monkeypatch):
    windsurf_dir = tmp_path / ".codeium" / "windsurf"
    windsurf_dir.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    results = install_mcp(platform="windsurf")
    assert len(results) == 1

    config = json.loads((windsurf_dir / "mcp_config.json").read_text())
    assert "agenteval" in config["mcpServers"]


def test_install_windsurf_skips_when_no_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    results = install_mcp(platform="windsurf")
    assert len(results) == 0


def test_install_preserves_existing_config(tmp_path, monkeypatch):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    existing = {"mcpServers": {"other-server": {"command": "other"}}, "extraKey": True}
    (claude_dir / "settings.json").write_text(json.dumps(existing))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    install_mcp(platform="claude-code")

    config = json.loads((claude_dir / "settings.json").read_text())
    assert "other-server" in config["mcpServers"]
    assert "agenteval" in config["mcpServers"]
    assert config["extraKey"] is True
