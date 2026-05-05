from __future__ import annotations

import json
from pathlib import Path

from codex.services.market_cycle_engine import infer_market_cycle
from codex.services.market_structure_detector import analyze_land_structure
from codex.services.sqlite_land_warehouse import query_land_records


OUTPUT_PATH = Path("data/storage/reports/city_investment_retreat_report.json")


TOPIC = "城投拿地变化"


def run() -> None:
    records = query_land_records(limit=1000)

    structure = analyze_land_structure(records)

    cycle_text = " ".join(signal["signal"] for signal in structure.get("signals", []))
    cycle = infer_market_cycle(cycle_text)

    report = {
        "topic": TOPIC,
        "structure_analysis": structure,
        "market_cycle": cycle,
        "story_angle": build_story_angle(structure, cycle),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved report → {OUTPUT_PATH}")


def build_story_angle(structure: dict, cycle: dict) -> str:
    signals = structure.get("signals", [])

    if any(s["type"] == "city_investment_decline" for s in signals):
        return "城投拿地占比下降，土地市场结构可能正在重新变化。"

    if cycle.get("cycle") == "recovery":
        return "市场风险偏好可能开始恢复。"

    return "土地市场仍处于结构调整阶段。"


if __name__ == "__main__":
    run()
