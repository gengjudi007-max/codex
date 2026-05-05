from __future__ import annotations

from datetime import datetime


PIPELINE_STEPS = [
    "抓取城市土地数据",
    "保存原始数据",
    "数据质量检查",
    "写入 SQLite 仓库",
    "生成城市分化指数",
    "生成新闻信号",
    "生成自动选题",
    "生成日报/深度稿",
]


def run() -> None:
    print("Codex Daily Scheduler")
    print("=" * 28)
    print(f"run_time: {datetime.now().isoformat(timespec='seconds')}")
    print("\nPlanned pipeline:")
    for idx, step in enumerate(PIPELINE_STEPS, start=1):
        print(f"{idx}. {step}")

    print("\nFuture scheduler suggestions:")
    print("- cron")
    print("- launchd (macOS)")
    print("- GitHub Actions")
    print("- Airflow / Prefect")


if __name__ == "__main__":
    run()
