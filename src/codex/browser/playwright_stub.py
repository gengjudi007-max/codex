from __future__ import annotations

from typing import Dict


class BrowserAutomationNotInstalled(RuntimeError):
    pass


def describe_browser_strategy() -> Dict:
    return {
        "goal": "自动获取 cookie、token、动态 payload",
        "recommended_stack": ["playwright", "chromium"],
        "scenarios": [
            "上海土地市场",
            "深圳土地交易系统",
            "需要登录或动态token的政务网站",
        ],
        "future_capabilities": [
            "自动登录",
            "自动翻页",
            "自动导出 CSV",
            "自动抓取 network 请求",
        ],
    }


def ensure_playwright_ready() -> None:
    raise BrowserAutomationNotInstalled(
        "Playwright 自动化尚未安装。后续可执行: python -m pip install playwright && playwright install chromium"
    )
