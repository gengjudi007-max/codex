from __future__ import annotations

from typing import Dict, List


DEFAULT_REPORTER_TASKS = [
    "识别市场异动",
    "寻找城市分化",
    "追踪房企行为",
    "生成采访问题",
    "寻找市场矛盾",
]


INTERVIEW_QUESTION_TEMPLATES = [
    "为什么当前市场出现这一变化？",
    "这一变化与过去一年相比有何不同？",
    "企业当前策略是否发生变化？",
    "政策是否开始影响市场？",
]


CONFLICT_PATTERNS = [
    ("土地热度上升", "成交疲弱"),
    ("高溢价拿地", "销售承压"),
    ("政策宽松", "市场恢复缓慢"),
]


def generate_interview_questions(topic: str) -> List[str]:
    return [f"{topic}：{question}" for question in INTERVIEW_QUESTION_TEMPLATES]


def detect_possible_conflicts(text: str) -> List[str]:
    results = []
    for left, right in CONFLICT_PATTERNS:
        if left in text or right in text:
            results.append(f"市场可能存在‘{left}’与‘{right}’之间的背离。")
    return results


def build_reporter_agent_output(topic: str, article_text: str) -> Dict:
    return {
        "topic": topic,
        "tasks": DEFAULT_REPORTER_TASKS,
        "interview_questions": generate_interview_questions(topic),
        "conflicts": detect_possible_conflicts(article_text),
    }
