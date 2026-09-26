from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex.interaction import analyze_payload

from codex.services.continuous_runner import run_loop, run_once
from codex.services.control_center import build_control_center
from codex.services.executive_intelligence import run_executive_intelligence
from codex.services.health_check import run_health_check
from codex.services.newsroom_desk import run_newsroom_desk
from codex.services.realtime_pipeline import run_realtime_pipeline


parser = argparse.ArgumentParser(prog="codex")
subparsers = parser.add_subparsers(dest="command")

health_parser = subparsers.add_parser("health")
health_parser.add_argument("--config", default="config/watchlist.json")

run_once_parser = subparsers.add_parser("run-once")
run_once_parser.add_argument("--config", default="config/watchlist.json")

loop_parser = subparsers.add_parser("run-loop")
loop_parser.add_argument("--config", default="config/watchlist.json")
loop_parser.add_argument("--interval", type=int, default=3600)
loop_parser.add_argument("--max-runs", type=int, default=1)

newsroom_parser = subparsers.add_parser("newsroom-desk")
newsroom_parser.add_argument("--config", default="config/watchlist.json")

subparsers.add_parser("control-center")
subparsers.add_parser("executive")
subparsers.add_parser("pipeline")
report_parser = subparsers.add_parser("report", help="从带来源的 JSON 生成可追溯正文")
report_parser.add_argument("--input", required=True)
report_parser.add_argument("--writer", choices=["extractive", "model"], default=None)
report_parser.add_argument("--output", help="保存正文为 UTF-8 Markdown")


def main() -> None:
    args = parser.parse_args()

    if args.command == "report":
        try:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("输入须为 JSON 对象")
            if args.writer:
                payload["writer"] = args.writer
            result = analyze_payload({**payload, "mode": "report"})
            if "error" in result:
                raise ValueError(result["error"])
            report = result["result"]
            if not report["article_text"]:
                raise ValueError("缺少来源正文，无法成稿")
            if args.output:
                if Path(args.output).resolve() == Path(args.input).resolve():
                    raise ValueError("输出不能覆盖输入材料")
                Path(args.output).write_text(report["article_text"], encoding="utf-8")
        except (OSError, ValueError) as exc:
            parser.exit(2, f"成稿失败：{exc}\n")
    elif args.command == "health":
        result = run_health_check(args.config)
    elif args.command == "run-once":
        result = run_once(args.config)
    elif args.command == "run-loop":
        result = run_loop(args.config, interval_seconds=args.interval, max_runs=args.max_runs)
    elif args.command == "newsroom-desk":
        result = run_newsroom_desk(args.config)
    elif args.command == "control-center":
        result = build_control_center()
    elif args.command == "executive":
        result = run_executive_intelligence()
    elif args.command == "pipeline":
        result = run_realtime_pipeline({"connectors": []})
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
