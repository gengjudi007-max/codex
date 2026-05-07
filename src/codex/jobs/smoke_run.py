from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


OUTPUT_PATH = Path("data/storage/reports/smoke_run_report.json")


PIPELINE = [
    ["codex.jobs.doctor"],
    ["codex.jobs.fetch_beijing_land_data"],
    ["codex.jobs.load_land_to_warehouse", "--input", "data/processed/beijing_land_items.json"],
    ["codex.jobs.city_investment_retreat_report"],
    ["codex.jobs.city_divergence_report"],
    ["codex.jobs.news_signal_report"],
    ["codex.jobs.daily_newsroom_run"],
    ["codex.jobs.newsroom_dashboard"],
]


def run_module(module_args: List[str]) -> Dict:
    module = module_args[0]
    cmd = [sys.executable, "-m", *module_args]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "module": module,
        "cmd": " ".join(cmd),
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def run() -> Dict:
    results = []
    for step in PIPELINE:
        print(f"\n=== Running {' '.join(step)} ===")
        result = run_module(step)
        results.append(result)
        print(result["stdout"])
        if result["stderr"]:
            print(result["stderr"])
        if not result["ok"]:
            print(f"Step failed: {result['module']}")
            break

    report = {
        "run_time": datetime.now().isoformat(timespec="seconds"),
        "ok": all(item["ok"] for item in results),
        "results": results,
        "expected_outputs": [
            "data/processed/beijing_land_items.json",
            "data/storage/codex.db",
            "data/storage/reports/city_investment_retreat_report.json",
            "data/storage/reports/city_divergence_report.json",
            "data/storage/reports/news_signal_report.json",
            "data/storage/newsroom/daily_story.json",
            "data/storage/dashboard/newsroom_dashboard.html",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSmoke run report saved → {OUTPUT_PATH}")
    return report


if __name__ == "__main__":
    run()
