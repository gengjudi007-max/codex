from __future__ import annotations

from typing import Any, Dict, List

DEFAULT_ITEMS: List[Dict[str, Any]] = [
    {
        "source": "policy",
        "title": "政治局会议提出努力稳定房地产市场",
        "summary": "政策强调努力稳定房地产市场，后续地方可能继续因城施策。",
    },
    {
        "source": "announcement",
        "company": "保利发展",
        "title": "保利发展净利润同比下降40%",
        "summary": "利润下滑与资产减值增加，经营现金流仍需观察。",
    },
    {
        "source": "land",
        "city": "武汉",
        "title": "武汉土拍城投占比超70%",
        "summary": "土地市场仍依赖地方平台托底，需追踪后续开工和收储路径。",
    },
]


def error_response(message: str, mode: str = "unknown") -> Dict[str, Any]:
    return {
        "mode": mode,
        "error": message,
        "result": None,
    }


def require_list(payload: Dict[str, Any], key: str) -> tuple[bool, str]:
    if not isinstance(payload.get(key), list):
        return False, f"{key} 必须是列表。"
    return True, ""
