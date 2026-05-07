from __future__ import annotations

import argparse
import json

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


def main() -> None:
    args = parser.parse_args()

    if args.command == "health":
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
