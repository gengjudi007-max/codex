from dataclasses import dataclass
from typing import Any, Dict, List

from codex.services.text_utils import infer_city, infer_company, infer_region, normalize_text


@dataclass
class TopicRule:
    """房地产报道选题规则。"""

    name: str
    category: str
    keywords: List[str]
    topic_template: str
    angle: str
    reason: str
    score: int
    materials: List[str]
    interview_targets: List[str]
    questions: List[str]

    def match(self, item: Dict[str, Any]) -> bool:
        text = _normalize_text(item)
        return any(keyword in text for keyword in self.keywords)

    def build_topic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "topic": self.topic_template.format(**_safe_item(item)),
            "category": self.category,
            "angle": self.angle,
            "reason": self.reason,
            "score": self.score,
            "source": item.get("source", "unknown"),
            "source_url": item.get("url") or item.get("source_url"),
            "trigger": item.get("title") or item.get("summary") or "未命名信息源",
            "materials": self.materials,
            "interview_targets": self.interview_targets,
            "questions": self.questions,
            "input_item": item,
        }


def _safe_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = _normalize_text(item)
    return {
        "title": item.get("title", "相关动态"),
        "company": item.get("company") or infer_company(text) or "相关企业",
        "city": item.get("city") or infer_city(text) or "相关城市",
        "region": item.get("region") or infer_region(text) or "相关区域",
    }


def _normalize_text(item: Dict[str, Any]) -> str:
    values = []
    for key in ("title", "summary", "content", "keywords", "company", "city", "region"):
        values.append(normalize_text(item.get(key, "")))
    return " ".join(values)


REAL_ESTATE_TOPIC_RULES: List[TopicRule] = [
    TopicRule(
        name="policy_language_shift",
        category="政策解读",
        keywords=["努力稳定", "着力稳定", "促进房地产市场平稳健康发展", "止跌回稳", "因城施策"],
        topic_template="{title}：房地产政策表述变化背后的市场信号",
        angle="对比中央和地方政策表述变化，判断政策边际力度、调控重心和市场预期变化。",
        reason="房地产政策措辞变化往往反映政策目标、执行力度和风险判断的微妙调整。",
        score=90,
        materials=["政策原文", "前次同类政策表述", "住建部/央行/金融监管部门表态", "地方跟进政策", "市场成交和价格数据"],
        interview_targets=["政策研究人士", "房地产研究机构分析师", "房企投研人士", "地方住建系统人士"],
        questions=[
            "本次政策表述与此前相比，最关键的变化是什么？",
            "这种变化是力度增强、边际转向，还是执行口径调整？",
            "地方政府和金融机构后续可能如何跟进？",
        ],
    ),
    TopicRule(
        name="developer_profit_pressure",
        category="房企经营",
        keywords=["净利润下降", "亏损", "毛利率下降", "减值", "资产减值", "债务重组", "流动性压力"],
        topic_template="{company}业绩承压：房地产企业盈利模式继续重估",
        angle="从利润、毛利率、减值、债务和经营现金流拆解房企真实经营质量。",
        reason="房企利润波动能够反映行业出清阶段的经营压力和商业模式变化。",
        score=88,
        materials=["年度报告/中期报告", "业绩公告", "债券公告", "评级报告", "同行业可比公司财务数据"],
        interview_targets=["房企财务人士", "地产债分析师", "会计师/审计人士", "机构投资者"],
        questions=[
            "利润下降主要来自销售下滑、毛利率下行，还是资产减值？",
            "现金流是否比利润表更能反映企业真实状态？",
            "该企业与同行相比，压力主要来自哪里？",
        ],
    ),
    TopicRule(
        name="land_market_soes_city_investment",
        category="土地市场",
        keywords=["城投拿地", "土拍", "土地市场", "溢价率", "拿地", "底价成交", "流拍", "托底", "地方平台", "土地财政", "集中供地"],
        topic_template="{city}土地市场变化：城投托底与土地财政压力再观察",
        angle="分析城投拿地占比、成交溢价率、流拍率和地块后续开发状态，判断土地市场真实热度。",
        reason="土地市场是房地产周期和地方财政压力的重要前置信号。",
        score=92,
        materials=["自然资源部门成交公告", "土地出让文件", "专项债募集说明书", "地方城投公告", "中指/克而瑞等机构数据"],
        interview_targets=["地方自然资源系统人士", "城投公司人士", "土地市场研究员", "开发商投资拓展人士"],
        questions=[
            "城投拿地是市场化投资，还是承担托底功能？",
            "这些地块后续是否实质开发，资金来源是什么？",
            "土地成交结构变化对地方财政意味着什么？",
        ],
    ),
    TopicRule(
        name="housing_and_urban_renewal",
        category="城市更新与住房问题",
        keywords=["城中村改造", "城市更新", "老旧小区改造", "保障房", "保租房", "住房问题", "老破小"],
        topic_template="{city}城市更新样本：住房改善、资金平衡与商业模式难题",
        angle="从居民诉求、政府投入、社会资本参与和项目回报机制分析城市更新项目可持续性。",
        reason="城市更新正在成为存量时代房地产行业的重要叙事和投资方向。",
        score=86,
        materials=["项目实施方案", "招投标文件", "专项债文件", "地方政府公告", "居民访谈", "开发主体资料"],
        interview_targets=["居民/业主", "项目操盘方", "地方街道或住建部门", "城市更新研究者"],
        questions=[
            "项目资金从哪里来，如何实现平衡？",
            "居民诉求与商业回报之间如何协调？",
            "社会资本参与的边界和收益模式是什么？",
        ],
    ),
    TopicRule(
        name="real_estate_finance_innovation",
        category="不动产金融",
        keywords=["REITs", "CMBS", "ABS", "经营性物业贷", "融资协调机制", "白名单", "债券展期", "再融资"],
        topic_template="不动产金融工具变化：{company}融资动作的行业参照意义",
        angle="分析融资工具背后的资产质量、现金流、监管导向和行业融资环境变化。",
        reason="不动产金融工具变化能够反映房企、商业资产和金融机构之间的风险再定价。",
        score=84,
        materials=["融资公告", "募集说明书", "交易所问询", "评级报告", "底层资产资料", "同类融资案例"],
        interview_targets=["不动产金融人士", "券商资管人士", "评级机构分析师", "企业融资负责人"],
        questions=[
            "该融资工具解决的是短期流动性还是长期资产盘活问题？",
            "底层资产现金流是否足以支撑融资安排？",
            "这一案例是否具备行业复制性？",
        ],
    ),
    TopicRule(
        name="property_service_cycle",
        category="物业服务",
        keywords=["物业", "在管面积", "合同面积", "撤场", "退出低效项目", "增值服务", "应收账款"],
        topic_template="物业行业从扩张转向收缩：{company}动作释放的新周期信号",
        angle="从在管面积、合同面积、应收账款、项目退出和增值服务变化观察物业企业战略收缩。",
        reason="物业企业从规模竞赛转向质量经营，是房地产下行后的重要产业链变化。",
        score=82,
        materials=["物业公司年报", "项目退出公告", "应收账款数据", "母公司关联交易", "同行对比数据"],
        interview_targets=["物业公司管理层", "项目经理", "业委会人士", "行业研究员"],
        questions=[
            "退出低效项目的标准是什么？",
            "规模收缩是否会改善利润率和现金流？",
            "物业企业未来增长靠基础物业还是增值服务？",
        ],
    ),
]


def find_topics(input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从政策、公告、市场数据等输入中识别房地产新闻选题。"""
    items = input_data.get("items", [])
    topics: List[Dict[str, Any]] = []

    for item in items:
        for rule in REAL_ESTATE_TOPIC_RULES:
            if rule.match(item):
                topics.append(rule.build_topic(item))

    topics.sort(key=lambda topic: topic["score"], reverse=True)
    return topics
