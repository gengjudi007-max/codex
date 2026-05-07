from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Dict

from codex.api_gateway import main as run_api_gateway

APP_NAME = "NewsroomOS"


def app_data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_local_dirs() -> Dict[str, str]:
    root = app_data_dir()
    dirs = {
        "root": root,
        "data": root / "data",
        "logs": root / "logs",
        "cache": root / "cache",
        "exports": root / "exports",
    }
    for path in dirs.values():
        Path(path).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("NEWSROOM_OS_HOME", str(root))
    return {key: str(value) for key, value in dirs.items()}


def launch_desktop() -> None:
    dirs = ensure_local_dirs()
    host = "127.0.0.1"
    port = int(os.environ.get("NEWSROOM_OS_PORT", "8000"))
    url = f"http://{host}:{port}/control-center"

    thread = threading.Thread(target=run_api_gateway, kwargs={"host": host, "port": port}, daemon=True)
    thread.start()

    print("Newsroom OS Desktop Runtime")
    print(f"Local data directory: {dirs['root']}")
    print(f"Opening dashboard endpoint: {url}")
    webbrowser.open(url)
    thread.join()


def main() -> None:
    launch_desktop()


if __name__ == "__main__":
    main()
