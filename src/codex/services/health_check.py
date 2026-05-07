from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_MODULES = [
    "codex.interaction",
    "codex.services.source_ingestion",
    "codex.services.continuous_runner",
    "codex.services.newsroom_desk",
    "codex.services.fact_check_engine",
    "codex.services.newsroom_orchestrator",
]

OPTIONAL_MODULES = ["pypdf", "requests"]


def run_health_check(config_path: str = "config/watchlist.json") -> Dict[str, Any]:
    checks = []
    checks.extend(_module_checks(REQUIRED_MODULES, required=True))
    checks.extend(_module_checks(OPTIONAL_MODULES, required=False))
    checks.append(_config_check(config_path))
    checks.append(_path_writable_check("data"))
    checks.append(_path_writable_check("data/run_logs"))

    failed = [check for check in checks if check["status"] == "failed"]
    warnings = [check for check in checks if check["status"] == "warning"]

    return {
        "mode": "health_check",
        "overall_status": "failed" if failed else ("warning" if warnings else "ok"),
        "checks": checks,
        "summary": {
            "ok": sum(1 for check in checks if check["status"] == "ok"),
            "warning": len(warnings),
            "failed": len(failed),
        },
        "next_actions": _next_actions(failed, warnings),
    }


def _module_checks(module_names: List[str], required: bool) -> List[Dict[str, Any]]:
    checks = []
    for name in module_names:
        try:
            importlib.import_module(name)
            checks.append({"name": f"module:{name}", "status": "ok", "required": required})
        except Exception as exc:  # noqa: BLE001
            checks.append(
                {
                    "name": f"module:{name}",
                    "status": "failed" if required else "warning",
                    "required": required,
                    "error": str(exc),
                }
            )
    return checks


def _config_check(config_path: str) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        example = Path("config/watchlist.example.json")
        return {
            "name": "config:watchlist",
            "status": "warning",
            "message": f"未找到 {config_path}。可从 {example} 复制。",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"name": "config:watchlist", "status": "failed", "error": f"JSON 格式错误：{exc}"}
    if not isinstance(payload, dict):
        return {"name": "config:watchlist", "status": "failed", "error": "配置顶层必须是对象。"}
    for key in ("sources", "texts", "items", "paths"):
        if key in payload and not isinstance(payload[key], list):
            return {"name": "config:watchlist", "status": "failed", "error": f"{key} 必须是列表。"}
    return {"name": "config:watchlist", "status": "ok", "path": str(path)}


def _path_writable_check(path_text: str) -> Dict[str, Any]:
    path = Path(path_text)
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".codex_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return {"name": f"path:{path_text}", "status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"name": f"path:{path_text}", "status": "failed", "error": str(exc)}


def _next_actions(failed: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> List[str]:
    actions = []
    if failed:
        actions.append("先修复 failed 项；否则 newsroom OS 不应进入持续运行。")
    if any(check["name"] == "config:watchlist" for check in warnings):
        actions.append("复制 config/watchlist.example.json 为 config/watchlist.json，并替换真实监控源。")
    if any("pypdf" in check["name"] for check in warnings):
        actions.append("如需解析 PDF，请安装 pypdf：pip install pypdf。")
    if not actions:
        actions.append("健康检查通过，可运行 codex-health、codex-run-once 或 codex-newsroom-desk。")
    return actions
