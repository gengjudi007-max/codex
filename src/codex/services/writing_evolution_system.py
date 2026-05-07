from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from codex.services.style_learning_system import StyleLearningSystem, build_default_user_style_profile
from codex.services.topic_competitiveness_engine import TopicCompetitivenessEngine


@dataclass
class WritingEvolutionReport:
    period: str
    article_count: int
    dominant_article_types: List[str]
    topic_patterns: List[str]
    structure_patterns: List[str]
    style_strengths: List[str]
    style_weaknesses: List[str]
    evolution_signals: List[str]
    recommended_upgrades: List[str]
    updated_style_profile: Dict[str, Any]


class WritingEvolutionSystem:
    """个人写作进化系统。

    目标：
    - 定期复盘用户已完成稿件；
    - 识别选题、结构、表达、风险控制的变化；
    - 总结用户写作能力的强项和弱项；
    - 更新个人风格画像；
    - 反向优化模型调度、自动出稿和风格控制。
    """

    def __init__(self) -> None:
        self.style_system = StyleLearningSystem()
        self.topic_engine = TopicCompetitivenessEngine()

    def analyze_writing_history(
        self,
        articles: List[Dict[str, Any]],
        period: Optional[str] = None,
        previous_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        period = period or datetime.now().strftime("%Y-%m")
        profile = self.style_system.build_profile(articles, profile_name=f"财经地产写作进化画像-{period}") if articles else build_default_user_style_profile()
        if previous_profile:
            profile = self._merge_profiles(previous_profile, profile)

        report = WritingEvolutionReport(
            period=period,
            article_count=len(articles),
            dominant_article_types=self._dominant_article_types(articles),
            topic_patterns=self._topic_patterns(articles),
            structure_patterns=self._structure_patterns(articles),
            style_strengths=self._style_strengths(articles),
            style_weaknesses=self._style_weaknesses(articles),
            evolution_signals=self._evolution_signals(articles, previous_profile, profile),
            recommended_upgrades=self._recommended_upgrades(articles),
            updated_style_profile=profile,
        )
        return asdict(report)

    def build_personal_improvement_plan(self, evolution_report: Dict[str, Any]) -> Dict[str, Any]:
        """根据写作进化报告生成个人提升计划。"""
        weaknesses = evolution_report.get("style_weaknesses", [])
        upgrades = evolution_report.get("recommended_upgrades", [])

        tasks = []
        if any("抽象" in item for item in weaknesses):
            tasks.append({
                "goal": "降低抽象概念密度",
                "practice": "每个小标题至少补入2个具体主体：城市、企业、项目、受访者或数据。",
                "check": "段落中‘结构、趋势、逻辑、机制’等词出现过多时，要求替换为事实。",
            })
        if any("结构" in item for item in weaknesses):
            tasks.append({
                "goal": "强化小标题功能",
                "practice": "每个小标题只解决一个问题，避免原因、影响、展望三段论。",
                "check": "检查每个小标题是否能独立回答一个新闻问题。",
            })
        if any("风险" in item for item in weaknesses):
            tasks.append({
                "goal": "加强合规表达",
                "practice": "涉及品质、维权、违规等内容时，统一改为‘争议、情况有待核验、公开资料显示’。",
                "check": "终稿前运行Final Check和Style Control。",
            })
        if not tasks:
            tasks.append({
                "goal": "保持稳定输出",
                "practice": "每周选择1篇满意稿件加入风格样本库。",
                "check": "每月更新一次个人风格画像。",
            })

        return {
            "period": evolution_report.get("period"),
            "priority_tasks": tasks,
            "system_upgrades": upgrades,
            "next_review_cycle": "建议每月复盘一次，重大专题结束后单独复盘。",
        }

    def adapt_orchestration_rules(self, evolution_report: Dict[str, Any]) -> Dict[str, Any]:
        """根据写作进化结果反向调整模型调度偏好。"""
        article_types = evolution_report.get("dominant_article_types", [])
        weaknesses = evolution_report.get("style_weaknesses", [])
        topic_patterns = evolution_report.get("topic_patterns", [])

        preferences = {
            "default_article_type": article_types[0] if article_types else "深度报道",
            "max_primary_models_per_article": 1,
            "max_support_models_per_article": 3,
            "prefer_models": [],
            "suppress_models": [],
            "style_constraints": [],
        }

        if any("公司" in item or "房企" in item for item in topic_patterns):
            preferences["prefer_models"].append("developer_behavior")
        if any("城市" in item or "楼市" in item for item in topic_patterns):
            preferences["prefer_models"].append("city_divergence")
        if any("趋势" in item or "传导" in item for item in topic_patterns):
            preferences["prefer_models"].append("trend_evolution")
        if any("抽象" in item for item in weaknesses):
            preferences["style_constraints"].append("每段至少出现一个具体主体或数据点。")
        if any("模型堆叠" in item for item in weaknesses):
            preferences["suppress_models"].append("secondary_trend_layers")
            preferences["style_constraints"].append("单篇只保留一个核心逻辑。")

        preferences["prefer_models"] = list(dict.fromkeys(preferences["prefer_models"]))
        preferences["suppress_models"] = list(dict.fromkeys(preferences["suppress_models"]))
        return preferences

    def _dominant_article_types(self, articles: List[Dict[str, Any]]) -> List[str]:
        counts: Dict[str, int] = {}
        for article in articles:
            article_type = article.get("article_type", "深度报道")
            counts[article_type] = counts.get(article_type, 0) + 1
        return [item[0] for item in sorted(counts.items(), key=lambda x: x[1], reverse=True)]

    def _topic_patterns(self, articles: List[Dict[str, Any]]) -> List[str]:
        patterns = []
        text = " ".join([f"{a.get('title','')} {a.get('lead','')}" for a in articles])
        if any(k in text for k in ["房企", "利润", "年报", "销售"]):
            patterns.append("房企经营与利润结构")
        if any(k in text for k in ["城市", "楼市", "成交", "价格", "二手房"]):
            patterns.append("城市楼市与资产价格变化")
        if any(k in text for k in ["土地", "拿地", "城投", "土拍"]):
            patterns.append("土地市场与城投拿地")
        if any(k in text for k in ["政策", "政治局", "住建", "央行"]):
            patterns.append("政策语义与市场传导")
        if any(k in text for k in ["传导", "趋势", "重构", "分化"]):
            patterns.append("趋势传导与结构变化")
        return patterns or ["综合地产报道"]

    def _structure_patterns(self, articles: List[Dict[str, Any]]) -> List[str]:
        section_counts = [len(a.get("sections", [])) for a in articles]
        patterns = []
        if section_counts:
            avg = sum(section_counts) / len(section_counts)
            patterns.append(f"平均小标题数量约{avg:.1f}个")
            if 3 <= avg <= 5:
                patterns.append("结构符合深度报道常用区间")
            else:
                patterns.append("小标题数量需进一步稳定在3—5个")
        if any(len(a.get("lead", "")) > 250 for a in articles):
            patterns.append("导语偏向充分交代背景和问题")
        return patterns

    def _style_strengths(self, articles: List[Dict[str, Any]]) -> List[str]:
        strengths = []
        text = self._all_text(articles)
        if any(k in text for k in ["数据显示", "公开资料显示", "公告显示"]):
            strengths.append("数据和公开资料意识较强")
        if any(k in text for k in ["多位受访者", "一位", "人士称", "销售人员"]):
            strengths.append("具备采访主体和现场材料意识")
        if any(k in text for k in ["仍需观察", "有待核验", "尚需"]):
            strengths.append("风险边界表达较为克制")
        if any(k in text for k in ["利润来源", "行为路径", "传导", "分化"]):
            strengths.append("善于从结构和路径解释现象")
        return strengths or ["基础结构稳定"]

    def _style_weaknesses(self, articles: List[Dict[str, Any]]) -> List[str]:
        weaknesses = []
        text = self._all_text(articles)
        abstract_words = ["结构", "趋势", "逻辑", "机制", "分化", "重构", "修复", "韧性"]
        abstract_count = sum(text.count(word) for word in abstract_words)
        if text and abstract_count / max(len(text), 1) > 0.01:
            weaknesses.append("抽象概念词偏多，需补充更多事实、项目和采访主体")
        ai_phrases = ["整体来看", "可以看出", "本质上", "这意味着", "值得注意的是"]
        if any(phrase in text for phrase in ai_phrases):
            weaknesses.append("存在模板化或AI化连接表达")
        risk_phrases = ["违规", "造假", "牺牲品质", "偷工减料", "暴雷"]
        if any(phrase in text for phrase in risk_phrases):
            weaknesses.append("存在潜在高风险定性表达")
        if any(len(a.get("sections", [])) > 5 for a in articles):
            weaknesses.append("部分稿件结构过重，存在模型堆叠风险")
        return weaknesses or ["暂无明显短板，建议继续积累样本"]

    def _evolution_signals(
        self,
        articles: List[Dict[str, Any]],
        previous_profile: Optional[Dict[str, Any]],
        profile: Dict[str, Any],
    ) -> List[str]:
        signals = []
        if not previous_profile:
            return ["已建立初始个人风格画像。"]
        if profile.get("examples_count", 0) > previous_profile.get("examples_count", 0):
            signals.append("风格样本数量增加，画像稳定性提升。")
        if set(profile.get("article_types", [])) != set(previous_profile.get("article_types", [])):
            signals.append("稿件类型覆盖发生变化，模型调度偏好需同步更新。")
        if not signals:
            signals.append("风格画像变化不大，建议继续补充高质量终稿样本。")
        return signals

    def _recommended_upgrades(self, articles: List[Dict[str, Any]]) -> List[str]:
        weaknesses = self._style_weaknesses(articles)
        upgrades = []
        if any("抽象" in item for item in weaknesses):
            upgrades.append("在风格控制引擎中提高具体主体密度检测权重。")
        if any("AI" in item for item in weaknesses):
            upgrades.append("扩大禁用模板句库，强化段首表达检测。")
        if any("风险" in item for item in weaknesses):
            upgrades.append("对公司分析稿默认启用高风险审稿模式。")
        if any("模型堆叠" in item for item in weaknesses):
            upgrades.append("模型调度系统进一步限制深度稿辅助模型数量。")
        return upgrades or ["保持现有系统配置，每月复盘一次。"]

    def _merge_profiles(self, previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(current)
        for key in ["title_patterns", "lead_patterns", "section_patterns", "paragraph_rules", "preferred_phrases", "banned_phrases", "risk_rules", "structure_rules", "article_types"]:
            merged[key] = list(dict.fromkeys((previous.get(key, []) or []) + (current.get(key, []) or [])))
        merged["examples_count"] = previous.get("examples_count", 0) + current.get("examples_count", 0)
        return merged

    def _all_text(self, articles: List[Dict[str, Any]]) -> str:
        chunks = []
        for article in articles:
            chunks.append(article.get("title", ""))
            chunks.append(article.get("lead", ""))
            for section in article.get("sections", []):
                chunks.append(section.get("title", ""))
                chunks.append(section.get("content", ""))
        return " ".join(chunks)


def render_writing_evolution_report(report: Dict[str, Any]) -> str:
    parts = [
        f"写作进化报告｜{report.get('period')}",
        f"样本数量：{report.get('article_count')}",
        "主要稿件类型：" + "、".join(report.get("dominant_article_types", [])),
        "选题模式：" + "、".join(report.get("topic_patterns", [])),
        "结构特征：" + "、".join(report.get("structure_patterns", [])),
        "优势：" + "、".join(report.get("style_strengths", [])),
        "短板：" + "、".join(report.get("style_weaknesses", [])),
        "变化信号：" + "、".join(report.get("evolution_signals", [])),
        "建议升级：" + "、".join(report.get("recommended_upgrades", [])),
    ]
    return "\n".join(parts)
