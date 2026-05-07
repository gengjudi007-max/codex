from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, List


REQUIRED_PACKAGES = ["requests", "bs4"]
RECOMMENDED_FILES = [
    "pyproject.toml",
    "src/codex/daily_run.py",
    "src/codex/jobs/fetch_beijing_land_data.py",
    "src/codex/connectors/beijing_land_connector.py",
]


def run_runtime_diagnostics(project_root: Path | str = ".") -> Dict:
    """检查本地运行环境，定位常见问题。

    重点覆盖：
    - 是否在项目根目录；
    - 是否使用虚拟环境；
    - 依赖是否安装；
    - curl 是否可用；
    - src/codex 结构是否存在。
    """
    root = Path(project_root).resolve()
    missing_files = [path for path in RECOMMENDED_FILES if not (root / path).exists()]
    missing_packages = [pkg for pkg in REQUIRED_PACKAGES if importlib.util.find_spec(pkg) is None]

    return {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "project_root": str(root),
        "inside_virtualenv": sys.prefix != sys.base_prefix,
        "src_layout_detected": (root / "src" / "codex").exists(),
        "missing_files": missing_files,
        "missing_packages": missing_packages,
        "curl_available": shutil.which("curl") is not None,
        "status": build_status(missing_files, missing_packages),
    }


def build_status(missing_files: List[str], missing_packages: List[str]) -> str:
    if missing_files:
        return "project_root_error"
    if missing_packages:
        return "dependency_error"
    return "ok"


def render_diagnostics_report(result: Dict) -> str:
    lines = ["Codex runtime diagnostics", "=" * 28]
    for key in [
        "status",
        "project_root",
        "python_version",
        "python_executable",
        "inside_virtualenv",
        "src_layout_detected",
        "curl_available",
    ]:
        lines.append(f"{key}: {result.get(key)}")

    if result.get("missing_files"):
        lines.append("\nMissing project files:")
        lines.extend([f"- {item}" for item in result["missing_files"]])

    if result.get("missing_packages"):
        lines.append("\nMissing Python packages:")
        lines.extend([f"- {item}" for item in result["missing_packages"]])

    if result.get("status") == "project_root_error":
        lines.append("\nFix: cd 到包含 pyproject.toml、src、data 的项目根目录后再运行。")
    elif result.get("status") == "dependency_error":
        lines.append("\nFix: source .venv/bin/activate 后执行 python -m pip install -e .")
    else:
        lines.append("\nEnvironment looks ready.")

    return "\n".join(lines)
