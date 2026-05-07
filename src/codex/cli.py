from __future__ import annotations

import argparse
import json

from codex.services.continuous_runner import run_loop, run_once
from codex.services.health_check import run_health_check
from codex.services.newsroom_desk import run_newsroom_desk


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
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
