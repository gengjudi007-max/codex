from __future__ import annotations

import re
from typing import Dict, List


QUESTION_PATTERNS = [r"为什么", r"怎么看", r"是否", r"如何"]
EMOTION_PATTERNS = [r"担心", r"焦虑", r"乐观", r"悲观", r"压力"]


def structure_interview_material(text: str) -> Dict:
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

    quotes = extract_quotes(paragraphs)
    questions = extract_questions(paragraphs)
    emotions = extract_emotions(paragraphs)
    timelines = extract_timelines(paragraphs)

    return {
        "paragraph_count": len(paragraphs),
        "quotes": quotes,
        "questions": questions,
        "emotions": emotions,
        "timelines": timelines,
    }


def extract_quotes(paragraphs: List[str]) -> List[str]:
    results = []
    for paragraph in paragraphs:
        if "“" in paragraph or '"' in paragraph:
            results.append(paragraph)
    return results[:20]


def extract_questions(paragraphs: List[str]) -> List[str]:
    results = []
    for paragraph in paragraphs:
        for pattern in QUESTION_PATTERNS:
            if re.search(pattern, paragraph):
                results.append(paragraph)
                break
    return results[:20]


def extract_emotions(paragraphs: List[str]) -> List[str]:
    results = []
    for paragraph in paragraphs:
        for pattern in EMOTION_PATTERNS:
            if re.search(pattern, paragraph):
                results.append(paragraph)
                break
    return results[:20]


def extract_timelines(paragraphs: List[str]) -> List[str]:
    return [p for p in paragraphs if re.search(r"20\d{2}", p)][:20]
