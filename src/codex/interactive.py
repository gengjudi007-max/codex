from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from codex.interaction import analyze_payload


HELP = """可用输入：
  直接输入一段政策、公告、土地或融资信息
  /sample              运行内置样例
  /json 文件路径        读取 JSON 并自动选择模型
  /help                查看帮助
  /quit                退出
"""


def main() -> None:
    print("codex 房地产财经报道助手已连接。")
    print(HELP)

    while True:
        try:
            user_input = input("codex> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return

        if not user_input:
            continue
        if user_input in {"/quit", "quit", "exit"}:
            print("已退出。")
            return
        if user_input == "/help":
            print(HELP)
            continue
        if user_input == "/sample":
            _print_response(analyze_payload({}))
            continue
        if user_input.startswith("/json "):
            _load_json(user_input.removeprefix("/json ").strip())
            continue

        _print_response(analyze_payload({"message": user_input}))


def _load_json(path_text: str) -> None:
    path = Path(path_text).expanduser()
    if not path.exists():
        print(f"找不到文件：{path}")
        return

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"JSON 格式错误：{exc}")
        return

    if not isinstance(payload, dict):
        print("JSON 顶层需要是对象。")
        return

    _print_response(analyze_payload(payload))


def _print_response(response: Dict[str, Any]) -> None:
    if response.get("error"):
        print(f"\n错误：{response['error']}\n")
        return

    result = response.get("result", {})
    print(f"\n模式：{response.get('mode')}")

    if response.get("mode") == "topic_pipeline":
        print(result.get("message", ""))
        for index, topic in enumerate(result.get("topics", []), 1):
            print(f"\n[{index}] {topic.get('topic')}")
            print(f"优先级：{topic.get('priority')} | 评分：{topic.get('final_score')}")
            print(f"角度：{topic.get('angle')}")
            print("采访对象：" + "、".join(topic.get("interview_targets", [])))
            print("关键问题：")
            for question in topic.get("questions", []):
                print(f"- {question}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print()


if __name__ == "__main__":
    main()
