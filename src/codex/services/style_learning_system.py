from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class StyleProfile:
    """个人化写作风格画像。

    该画像不是简单模仿固定句式，而是学习：
    - 文章结构偏好；
    - 标题和导语节奏；
    - 小标题功能；
    - 段落长度与推进方式；
    - 风险表达边界；
    - 常用信息组织方式。
    """

    profile_name: str
    article_types: List[str]
    title_patterns: List[str]
    lead_patterns: List[str]
    section_patterns: List[str]
    paragraph_rules: List[str]
    preferred_phrases: List[str]
    banned_phrases: List[str]
    risk_rules: List[str]
    structure_rules: List[str]
    examples_count: int = 0


class StyleLearningSystem:
    """风格学习系统。

    使用方式：
    1. 输入你认可的历史稿件或终稿；
    2. 系统提取结构与语言偏好；
    3. 形成个人化风格画像；
    4. 后续稿件进入成稿/精校时，按该画像进行调整。

    注意：
    - 不复制原文表达；
    - 不机械套用句式；
    - 只学习结构、节奏、风险边界和表达习惯。
    """

    def build_profile(
        self,
        examples: List[Dict[str, Any]],
        profile_name: str = "财经地产深度报道风格",
    ) -> Dict[str, Any]:
        title_patterns = self._extract_title_patterns(examples)
        lead_patterns = self._extract_lead_patterns(examples)
        section_patterns = self._extract_section_patterns(examples)
        paragraph_rules = self._extract_paragraph_rules(examples)

        profile = StyleProfile(
            profile_name=profile_name,
            article_types=self._infer_article_types(examples),
            title_patterns=title_patterns,
            lead_patterns=lead_patterns,
            section_patterns=section_patterns,
            paragraph_rules=paragraph_rules,
            preferred_phrases=self._preferred_phrases(examples),
            banned_phrases=self._banned_phrases(),
            risk_rules=self._risk_rules(),
            structure_rules=self._structure_rules(),
            examples_count=len(examples),
        )
        return asdict(profile)

    def apply_profile(self, article: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """将个人化风格画像应用到稿件。"""
        revised = _normalize_article(article)
        revised["title"] = self._revise_title(revised.get("title", ""), profile)
        revised["lead"] = self._revise_lead(revised.get("lead", ""), profile)
        revised["sections"] = [
            {
                "title": self._revise_section_title(section.get("title", ""), profile),
                "content": self._revise_section_content(section.get("content", ""), profile),
            }
            for section in revised.get("sections", [])
        ]
        return {
            "revised_article": revised,
            "style_application_notes": self._application_notes(profile),
        }

    def compare_with_profile(self, article: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """检查稿件与个人风格画像的偏离程度。"""
        article = _normalize_article(article)
        issues = []

        section_count = len(article.get("sections", []))
        if section_count < 3 or section_count > 5:
            issues.append("小标题数量偏离常用深度报道结构，建议控制在3—5个。")

        if any(label in article.get("title", "") for label in ["标题", "导语"]):
            issues.append("成稿不应在正文中标注‘标题’或‘导语’字样。")

        for phrase in profile.get("banned_phrases", []):
            if _article_contains(article, phrase):
                issues.append(f"出现不符合风格的表达：{phrase}")

        abstract_density = self._abstract_density(article)
        if abstract_density > 0.08:
            issues.append("抽象概念词密度偏高，建议增加具体城市、企业、项目、数据和采访主体。")

        score = max(100 - len(issues) * 8, 0)
        return {
            "score": score,
            "issues": issues,
            "profile_name": profile.get("profile_name"),
        }

    def _extract_title_patterns(self, examples: List[Dict[str, Any]]) -> List[str]:
        patterns = []
        for example in examples:
            title = example.get("title", "")
            if "：" in title:
                patterns.append("主标题：副标题式，适用于深度稿和结构型报道")
            elif len(title) <= 18:
                patterns.append("短标题，强调判断和传播性")
            else:
                patterns.append("中长标题，直接点出主题和变化")
        return list(dict.fromkeys(patterns or ["标题简洁，避免口号化，优先呈现主题变化"]))

    def _extract_lead_patterns(self, examples: List[Dict[str, Any]]) -> List[str]:
        return [
            "导语以具体事件、数据或人物场景切入，再引出行业问题。",
            "导语控制在350—500字，避免一上来下结论。",
            "导语需要交代时间、主体、变化和后续问题。",
        ]

    def _extract_section_patterns(self, examples: List[Dict[str, Any]]) -> List[str]:
        return [
            "小标题承担独立信息功能，不使用机械的‘原因—影响—展望’模板。",
            "每个小标题围绕一个问题展开，避免多个模型并列堆叠。",
            "深度稿通常使用3—5个小标题，单个部分保持信息完整。",
        ]

    def _extract_paragraph_rules(self, examples: List[Dict[str, Any]]) -> List[str]:
        return [
            "段落以事实推进，先主体、再动作、再补充背景。",
            "同一段不同时承担数据、观点、结论三个功能。",
            "多用具体主体，如企业、城市、项目、受访者、机构；少用泛泛的‘市场’作主语。",
            "段落之间自然衔接，少使用‘整体来看、进一步来看、值得注意的是’等连接词。",
        ]

    def _preferred_phrases(self, examples: List[Dict[str, Any]]) -> List[str]:
        return [
            "数据显示",
            "公开资料显示",
            "多位受访者表示",
            "一位接近项目的人士称",
            "这一变化仍需继续观察",
            "相关情况仍需进一步核验",
        ]

    def _banned_phrases(self) -> List[str]:
        return [
            "整体来看",
            "可以看出",
            "本质上",
            "这意味着",
            "赋能",
            "助力",
            "打造",
            "高质量发展",
            "全面复苏",
            "彻底反转",
            "牺牲品质",
            "违规",
            "造假",
        ]

    def _risk_rules(self) -> List[str]:
        return [
            "涉及企业品质、维权、违规、减配等内容，只写已核验事实，不直接定性。",
            "未核验采访只作为线索，不进入正文核心事实。",
            "所有数据必须保留来源、统计口径和时间。",
            "趋势判断使用‘可能、仍需观察、需要继续核验’等边界表达。",
        ]

    def _structure_rules(self) -> List[str]:
        return [
            "成稿直接呈现标题、导语和小标题，不写‘标题’‘导语’标签。",
            "深度报道以标题、导语、3—5个小标题为主。",
            "单篇稿件只保留一个主模型和一条核心逻辑。",
            "结尾自然收束，不使用‘总结’‘结语’字样，除非用户明确要求。",
        ]

    def _infer_article_types(self, examples: List[Dict[str, Any]]) -> List[str]:
        types = []
        for example in examples:
            value = example.get("article_type")
            if value:
                types.append(value)
        return list(dict.fromkeys(types or ["深度报道", "公司分析", "政策解读", "观察稿"]))

    def _revise_title(self, title: str, profile: Dict[str, Any]) -> str:
        title = _tidy(title)
        for banned in profile.get("banned_phrases", []):
            title = title.replace(banned, "")
        return _tidy(title)

    def _revise_lead(self, lead: str, profile: Dict[str, Any]) -> str:
        lead = self._remove_banned(lead, profile)
        lead = lead.replace("本文将", "")
        lead = lead.replace("我们可以", "")
        return _tidy(lead)

    def _revise_section_title(self, title: str, profile: Dict[str, Any]) -> str:
        title = self._remove_banned(title, profile)
        title = title.replace("第一部分", "").replace("第二部分", "").replace("第三部分", "")
        return _tidy(title)

    def _revise_section_content(self, content: str, profile: Dict[str, Any]) -> str:
        content = self._remove_banned(content, profile)
        content = content.replace("综上所述，", "")
        content = content.replace("总而言之，", "")
        return _tidy(content)

    def _remove_banned(self, text: str, profile: Dict[str, Any]) -> str:
        revised = text or ""
        replacements = {
            "整体来看，": "",
            "可以看出，": "",
            "本质上，": "",
            "这意味着": "相关变化显示",
            "全面复苏": "部分指标改善",
            "彻底反转": "出现变化",
            "牺牲品质": "品质争议增加",
            "违规": "合规情况有待核验",
            "造假": "真实性有待核验",
        }
        for old, new in replacements.items():
            revised = revised.replace(old, new)
        for banned in profile.get("banned_phrases", []):
            revised = revised.replace(banned, "")
        return revised

    def _application_notes(self, profile: Dict[str, Any]) -> List[str]:
        return [
            f"已应用风格画像：{profile.get('profile_name')}",
            "已按第三方财经报道口径压制模板化表达。",
            "已保留风险边界，涉及未核验内容仍需人工复核。",
        ]

    def _abstract_density(self, article: Dict[str, Any]) -> float:
        text = " ".join([article.get("title", ""), article.get("lead", "")] + [s.get("content", "") for s in article.get("sections", [])])
        if not text:
            return 0.0
        abstract_words = ["结构", "逻辑", "趋势", "机制", "分化", "重构", "修复", "韧性", "赋能"]
        count = sum(text.count(word) for word in abstract_words)
        return count / max(len(text), 1)


def build_default_user_style_profile() -> Dict[str, Any]:
    """默认个人风格画像：适配财经/房地产深度报道。"""
    return asdict(
        StyleProfile(
            profile_name="财经地产深度报道个人风格",
            article_types=["深度报道", "公司分析", "政策解读", "观察稿", "评论社论"],
            title_patterns=["标题简洁、有判断，但不夸张定性", "可使用主副标题，但避免口号化"],
            lead_patterns=["导语350—500字", "以事实、数据、人物或项目切入", "导语提出问题，不提前给结论"],
            section_patterns=["3—5个小标题", "每个小标题解决一个问题", "小标题不机械套用原因、影响、展望"],
            paragraph_rules=["段落以事实推进", "每段尽量出现具体主体", "少用抽象总结句", "重要判断必须有数据或采访支撑"],
            preferred_phrases=["数据显示", "公开资料显示", "多位受访者表示", "仍需观察", "有待核验"],
            banned_phrases=["整体来看", "可以看出", "本质上", "这意味着", "赋能", "助力", "打造", "全面复苏", "牺牲品质", "违规", "造假"],
            risk_rules=["弱判断", "强事实", "涉及企业争议不定性", "未核验采访不直接引用"],
            structure_rules=["标题、导语、小标题直接呈现", "不写结语字样", "单篇只保留一个主模型"],
            examples_count=0,
        )
    )


def _normalize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": article.get("title", "").strip(),
        "lead": article.get("lead", "").strip(),
        "sections": [
            {"title": section.get("title", "").strip(), "content": section.get("content", "").strip()}
            for section in article.get("sections", [])
        ],
    }


def _article_contains(article: Dict[str, Any], phrase: str) -> bool:
    text = " ".join([article.get("title", ""), article.get("lead", "")] + [s.get("title", "") + s.get("content", "") for s in article.get("sections", [])])
    return phrase in text


def _tidy(text: str) -> str:
    cleaned = text or ""
    cleaned = cleaned.replace("。。", "。").replace("，，", "，")
    cleaned = cleaned.replace("\n\n\n", "\n\n")
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()
