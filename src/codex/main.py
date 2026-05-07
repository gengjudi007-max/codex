from __future__ import annotations

from typing import Any, Dict, List

from codex.interaction import DEFAULT_ITEMS, run_topic_pipeline
from codex.services.signal_monitor import monitor_signals


def run_daily_topic_engine(
    items: List[Dict[str, Any]] | None = None,
    *,
    verbose: bool = True,
) -> Dict[str, Any]:
    """每日自动选题主程序。"""
    items = items or DEFAULT_ITEMS
    topic_pipeline = run_topic_pipeline(items)
    signal_monitor = monitor_signals(items)
    result = {
        "topic_pipeline": topic_pipeline,
        "signal_monitor": signal_monitor,
    }

    if verbose:
        _print_daily_report(topic_pipeline, signal_monitor)

    return result


def _print_daily_report(
    topic_pipeline: Dict[str, Any],
    signal_monitor: Dict[str, Any],
) -> None:
    print("=== 今日房地产选题清单 ===")
    print(topic_pipeline["message"])

    for i, topic in enumerate(topic_pipeline["topics"], 1):
        print(f"\n[{i}] {topic['topic']}")
        print("优先级:", topic["priority"])
        print("评分:", topic["final_score"])
        print("核验状态:", topic["verification_status"], "| 置信度:", topic["confidence"])
        print("角度:", topic["angle"])
        print("必备材料:", "、".join(topic["material_plan"]["must_have"][:3]))
        print("采访对象:", "、".join(topic["interview_targets"]))
        print("问题:", "；".join(topic["questions"]))

    print("\n=== 今日信号监测 ===")
    for signal in signal_monitor["signals"][:5]:
        print(f"- {signal['title']}｜{signal['priority']}｜{','.join(signal['domains'])}")


if __name__ == "__main__":
    run_daily_topic_engine()
