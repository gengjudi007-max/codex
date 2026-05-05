from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


BANNED_AI_PHRASES = [
    "整体来看",
    "从数据来看",
    "从上述可以看出",
    "可以看出",
    "不难发现",
    "本质上",
    "这意味着",
    "值得注意的是",
    "需要指出的是",
    "进一步来看",
    "可以发现",
    "综上所述",
    "总而言之",
    "换言之",
    "释放出积极信号",
    "赋能",
    "助力",
    "打造",
    "高质量发展",
    "新篇章",
]

HIGH_RISK_ASSERTIONS = [
    "必然",
    "一定",
    "彻底",
    "全面复苏",
    "全面回暖",
    "已经反转",
    "崩盘",
    "暴雷",
    "违规",
    "造假",
    "恶意",
    "牺牲品质",
    "偷工减料",
]

ABSTRACT_WORDS = [
    "结构性",
    "韧性",
    "修复",
    "分化",
    "重构",
    "逻辑",
    "机制",
    "趋势",
]


@dataclass
class StyleIssue:
    level: str  # error | warning | note
    category: str
    phrase: str
    suggestion: str
    location: Optional[str] = None


@dataclass
class StyleControlReport:
    score: int
    issues: List[Dict[str, Any]]
    revised_article: Dict[str, Any]
    style_notes: List[str]


class StyleControlEngine:
    """写作风格控制引擎。

    目标：
    - 按稿件类型控制表达方式；
    - 去除明显AI模板表达；
    - 压制强判断和法律风险表述；
    - 保持财经深度报道的事实推进、结构克制和第三方视角；
    - 输出可供最终成稿引擎使用的修订稿。
    """

    def apply(
        self,
        article: Dict[str, Any],
        article_type: str = "深度报道",
        style: str = "经济观察报",
        risk_level: str = "medium",
    ) -> Dict[str, Any]:
        normalized = _normalize_article(article)
        issues = self._detect_issues(normalized, risk_level=risk_level)
        revised = self._revise_article(normalized, article_type=article_type, risk_level=risk_level)
        score = self._score(issues)
        notes = self._style_notes(article_type, style, risk_level)
        return asdict(
            StyleControlReport(
                score=score,
                issues=[asdict(issue) for issue in issues],
                revised_article=revised,
                style_notes=notes,
            )
        )

    def _detect_issues(self, article: Dict[str, Any], risk_level: str) -> List[StyleIssue]:
        issues: List[StyleIssue] = []
        blocks = _flatten_article(article)
        for block in blocks:
            text = block["text"]
            location = block["location"]
            for phrase in BANNED_AI_PHRASES:
                if phrase in text:
                    issues.append(
                        StyleIssue(
                            level="warning",
                            category="ai_pattern",
                            phrase=phrase,
                            suggestion="改为具体事实推进句，避免模板化分析表达。",
                            location=location,
                        )
                    )
            for phrase in HIGH_RISK_ASSERTIONS:
                if phrase in text:
                    issues.append(
                        StyleIssue(
                            level="error" if risk_level == "high" else "warning",
                            category="risk_assertion",
                            phrase=phrase,
                            suggestion="改为可核验的事实描述，避免未经充分证据支撑的定性。",
                            location=location,
                        )
                    )
            abstract_count = sum(text.count(word) for word in ABSTRACT_WORDS)
            if abstract_count >= 6:
                issues.append(
                    StyleIssue(
                        level="note",
                        category="abstract_density",
                        phrase="抽象词密度偏高",
                        suggestion="补充具体城市、企业、项目、数据或采访主体，减少概念堆叠。",
                        location=location,
                    )
                )
        return issues

    def _revise_article(self, article: Dict[str, Any], article_type: str, risk_level: str) -> Dict[str, Any]:
        revised = dict(article)
        revised["title"] = self._revise_text(article.get("title", ""), article_type, risk_level, is_title=True)
        revised["lead"] = self._revise_text(article.get("lead", ""), article_type, risk_level)
        sections = []
        for section in article.get("sections", []):
            sections.append(
                {
                    "title": self._revise_text(section.get("title", ""), article_type, risk_level, is_title=True),
                    "content": self._revise_text(section.get("content", ""), article_type, risk_level),
                }
            )
        revised["sections"] = sections
        return revised

    def _revise_text(self, text: str, article_type: str, risk_level: str, is_title: bool = False) -> str:
        revised = text or ""
        replacements = self._replacement_map(article_type, risk_level)
        for old, new in replacements.items():
            revised = revised.replace(old, new)

        if is_title:
            revised = self._revise_title(revised, article_type)
        else:
            revised = self._revise_paragraphs(revised, article_type)
        return _tidy_text(revised)

    def _replacement_map(self, article_type: str, risk_level: str) -> Dict[str, str]:
        replacements = {
            "整体来看，": "",
            "从数据来看，": "",
            "从上述可以看出，": "",
            "可以看出，": "",
            "不难发现，": "",
            "本质上，": "",
            "值得注意的是，": "",
            "需要指出的是，": "",
            "进一步来看，": "",
            "可以发现，": "",
            "综上所述，": "",
            "总而言之，": "",
            "这意味着": "相关变化显示",
            "全面复苏": "部分指标改善",
            "全面回暖": "部分市场活跃度提升",
            "已经反转": "出现变化",
            "必然": "可能",
            "一定": "可能",
            "彻底": "明显",
            "暴雷": "出现债务压力",
            "崩盘": "成交或价格明显下行",
            "违规": "合规情况有待核验",
            "造假": "真实性有待核验",
            "恶意": "相关行为有待核验",
            "牺牲品质": "品质争议增加",
            "偷工减料": "交付标准争议增加",
            "赋能": "支持",
            "助力": "推动",
            "打造": "建设",
            "开启新篇章": "出现新的变化",
        }
        if article_type in ["快讯", "短新闻"]:
            replacements.update({"可能": "仍需观察"})
        return replacements

    def _revise_title(self, title: str, article_type: str) -> str:
        title = title.replace("：", "：")
        if article_type in ["深度报道", "公司分析", "数据榜单"]:
            return title.strip()
        if article_type in ["快讯", "短新闻"]:
            for word in ["背后", "深层", "重构", "拐点"]:
                title = title.replace(word, "")
        return title.strip()

    def _revise_paragraphs(self, text: str, article_type: str) -> str:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        revised_paragraphs = []
        for paragraph in paragraphs:
            revised_paragraphs.append(self._revise_single_paragraph(paragraph, article_type))
        return "\n\n".join(revised_paragraphs)

    def _revise_single_paragraph(self, paragraph: str, article_type: str) -> str:
        paragraph = _tidy_text(paragraph)
        # 避免段首模板化。
        for prefix in ["与此同时，", "另一方面，", "此外，", "更重要的是，"]:
            if paragraph.startswith(prefix) and len(paragraph) > len(prefix) + 8:
                paragraph = paragraph[len(prefix):]
                break
        # 快讯压缩判断性连接。
        if article_type in ["快讯", "短新闻"]:
            paragraph = paragraph.replace("这一变化", "该信息")
            paragraph = paragraph.replace("后续仍需观察", "后续情况以官方披露为准")
        return _tidy_text(paragraph)

    def _score(self, issues: List[StyleIssue]) -> int:
        score = 100
        for issue in issues:
            if issue.level == "error":
                score -= 15
            elif issue.level == "warning":
                score -= 6
            else:
                score -= 2
        return max(score, 0)

    def _style_notes(self, article_type: str, style: str, risk_level: str) -> List[str]:
        notes = [
            "稿件结构以标题、导语和3—5个小标题为主，不在正文中标注“标题”“导语”等字样。",
            "模型只作为隐形结构，不在正文中显性出现模型、评分、系统判断等表述。",
            "段落推进优先使用事实、数据、采访主体和项目行为，少用概念总结。",
        ]
        if style == "经济观察报":
            notes.extend([
                "表达保持第三方视角，避免企业宣传口吻和口号化表达。",
                "每个小标题承担独立信息功能，避免机械三段论。",
                "结尾以事实余波和后续观察收束，少用宏大判断。",
            ])
        if risk_level == "high":
            notes.append("高风险稿件只写已核验事实，不对品质、维权、违规、减配等作直接定性。")
        return notes


def build_style_profile(article_type: str = "深度报道", style: str = "经济观察报") -> Dict[str, Any]:
    """生成稿件风格配置，供模型调度和成稿引擎调用。"""
    base = {
        "article_type": article_type,
        "style": style,
        "structure": ["标题", "导语", "3—5个小标题", "自然收束"],
        "tone": "第三方、克制、事实推进",
        "avoid": BANNED_AI_PHRASES + HIGH_RISK_ASSERTIONS,
        "prefer": [
            "具体主体",
            "公开数据",
            "采访对象",
            "项目行为",
            "时间变化",
            "范围限定",
        ],
    }
    if article_type == "评论社论":
        base["tone"] = "有判断但不空泛，观点集中，事实支撑"
        base["structure"] = ["问题", "判断", "论据", "政策或行业含义"]
    elif article_type in ["快讯", "短新闻"]:
        base["tone"] = "事实优先、少解释、不展开趋势"
        base["structure"] = ["事件", "数据", "来源", "背景"]
    elif article_type == "专题系列":
        base["tone"] = "连续跟踪、阶段推进、每篇只解决一个问题"
    return base


def render_style_report(report: Dict[str, Any]) -> str:
    """将风格控制结果转成编辑可读文本。"""
    parts = [f"风格评分：{report.get('score')}"]
    issues = report.get("issues", [])
    if issues:
        parts.append("问题提示：")
        for item in issues[:20]:
            parts.append(f"- {item.get('category')}｜{item.get('phrase')}｜{item.get('suggestion')}")
    notes = report.get("style_notes", [])
    if notes:
        parts.append("风格规则：")
        parts.extend([f"- {note}" for note in notes])
    return "\n".join(parts)


def _normalize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": article.get("title", "").strip(),
        "lead": article.get("lead", "").strip(),
        "sections": [
            {
                "title": section.get("title", "").strip(),
                "content": section.get("content", "").strip(),
            }
            for section in article.get("sections", [])
        ],
    }


def _flatten_article(article: Dict[str, Any]) -> List[Dict[str, str]]:
    blocks = []
    if article.get("title"):
        blocks.append({"location": "title", "text": article["title"]})
    if article.get("lead"):
        blocks.append({"location": "lead", "text": article["lead"]})
    for idx, section in enumerate(article.get("sections", []), 1):
        if section.get("title"):
            blocks.append({"location": f"section_{idx}_title", "text": section["title"]})
        if section.get("content"):
            blocks.append({"location": f"section_{idx}_content", "text": section["content"]})
    return blocks


def _tidy_text(text: str) -> str:
    cleaned = text or ""
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    cleaned = cleaned.replace("。。", "。")
    cleaned = cleaned.replace("，，", "，")
    cleaned = cleaned.replace("；。", "。")
    cleaned = cleaned.replace("\n\n\n", "\n\n")
    return cleaned.strip()
