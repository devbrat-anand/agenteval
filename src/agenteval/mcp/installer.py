"""MCP server installer for AI coding tools."""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path


def resolve_server_entry() -> dict:
    found = shutil.which("agenteval")
    if found:
        return {"command": found, "args": ["mcp", "serve"]}
    return {"command": sys.executable, "args": ["-m", "agenteval.cli.main", "mcp", "serve"]}


_INSTALLERS: dict[str, Callable[[], str | None]] = {}


def _register(name: str):
    def decorator(fn: Callable[[], str | None]) -> Callable[[], str | None]:
        _INSTALLERS[name] = fn
        return fn

    return decorator


def _upsert_json(path: Path, key: str, value: dict) -> None:
    existing = json.loads(path.read_text()) if path.exists() else {}
    servers = existing.setdefault(key, {})
    servers["agenteval"] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2) + "\n")


@_register("claude-code")
def _install_claude_code() -> str | None:
    path = Path.home() / ".claude" / "settings.json"
    if not path.parent.exists():
        return None
    _upsert_json(path, "mcpServers", resolve_server_entry())
    return str(path)


@_register("copilot")
def _install_copilot() -> str | None:
    path = Path.cwd() / ".vscode" / "mcp.json"
    if not path.parent.exists():
        return None
    _upsert_json(path, "servers", {**resolve_server_entry(), "type": "stdio"})
    return str(path)


@_register("cursor")
def _install_cursor() -> str | None:
    path = Path.cwd() / ".cursor" / "mcp.json"
    if not path.parent.exists():
        return None
    _upsert_json(path, "mcpServers", resolve_server_entry())
    return str(path)


@_register("windsurf")
def _install_windsurf() -> str | None:
    home = Path.home()
    candidates = [
        home / ".codeium" / "windsurf" / "mcp_config.json",
        home / ".windsurf" / "mcp_config.json",
    ]
    for path in candidates:
        if path.parent.exists():
            _upsert_json(path, "mcpServers", resolve_server_entry())
            return str(path)
    return None


def install_mcp(platform: str = "all") -> list[str]:
    results: list[str] = []
    targets = _INSTALLERS if platform == "all" else {platform: _INSTALLERS[platform]}
    for _name, fn in targets.items():
        try:
            path = fn()
            if path:
                results.append(path)
        except Exception:
            continue
    return results
