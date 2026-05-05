from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


INTERVIEW_ROLES = [
    "developer_sales",
    "developer_marketing",
    "buyer",
    "homeowner",
    "broker",
    "analyst",
    "policy_researcher",
    "government_staff",
    "city_investment_staff",
    "lawyer",
    "auditor",
    "other",
]


MATERIAL_STATUSES = [
    "raw",
    "checked",
    "usable",
    "background_only",
    "do_not_use",
]


@dataclass
class InterviewMaterial:
    """结构化采访素材。

    使用原则：
    1. 采访内容默认不直接当作事实依据，需要与数据、公告或多方说法交叉验证；
    2. 未授权具名的对象不得输出真实姓名；
    3. 涉及企业、项目、价格、销量等敏感信息时，应保留范围限定；
    4. status=do_not_use 的素材不得进入成稿。
    """

    material_id: str
    topic_tags: List[str]
    city: Optional[str]
    project: Optional[str]
    company: Optional[str]
    role: str
    speaker_label: str
    content: str
    date: str
    source_type: str = "interview"
    status: str = "raw"
    can_quote: bool = False
    quote_style: str = "paraphrase"  # direct | paraphrase | background
    verification: Optional[List[str]] = None
    risk_notes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


def create_interview_material(
    content: str,
    topic_tags: List[str],
    role: str,
    city: Optional[str] = None,
    project: Optional[str] = None,
    company: Optional[str] = None,
    speaker_label: Optional[str] = None,
    date: Optional[str] = None,
    can_quote: bool = False,
    quote_style: str = "paraphrase",
    status: str = "raw",
    verification: Optional[List[str]] = None,
    risk_notes: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """创建一条结构化采访素材。"""
    normalized_role = role if role in INTERVIEW_ROLES else "other"
    normalized_status = status if status in MATERIAL_STATUSES else "raw"
    today = date or datetime.now().strftime("%Y-%m-%d")
    material_id = _build_material_id(today, city, project, normalized_role, content)

    material = InterviewMaterial(
        material_id=material_id,
        topic_tags=topic_tags,
        city=city,
        project=project,
        company=company,
        role=normalized_role,
        speaker_label=speaker_label or _default_speaker_label(normalized_role),
        content=content.strip(),
        date=today,
        status=normalized_status,
        can_quote=can_quote,
        quote_style=quote_style,
        verification=verification or [],
        risk_notes=risk_notes or [],
        metadata=metadata or {},
    )
    return asdict(material)


def search_interview_materials(
    materials: List[Dict[str, Any]],
    topic: Optional[str] = None,
    city: Optional[str] = None,
    project: Optional[str] = None,
    company: Optional[str] = None,
    roles: Optional[List[str]] = None,
    require_usable: bool = True,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """按主题、城市、项目、企业和采访对象类型检索素材。"""
    scored = []
    for material in materials:
        if require_usable and material.get("status") not in ["checked", "usable", "background_only"]:
            continue
        if material.get("status") == "do_not_use":
            continue

        score = 0
        if topic:
            score += _topic_score(material, topic)
        if city and city == material.get("city"):
            score += 4
        if project and project == material.get("project"):
            score += 5
        if company and company == material.get("company"):
            score += 3
        if roles and material.get("role") in roles:
            score += 2
        if material.get("status") == "usable":
            score += 2
        if material.get("can_quote"):
            score += 1

        if score > 0 or not any([topic, city, project, company, roles]):
            scored.append((score, material))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def prepare_materials_for_article(
    materials: List[Dict[str, Any]],
    topic: str,
    section_titles: List[str],
) -> Dict[str, Any]:
    """为一篇稿件按小标题分配采访素材。"""
    usable = search_interview_materials(materials, topic=topic, require_usable=True, limit=100)
    allocation: Dict[str, List[Dict[str, Any]]] = {title: [] for title in section_titles}
    unused = []

    for material in usable:
        best_title = None
        best_score = 0
        for title in section_titles:
            score = _section_match_score(material, title)
            if score > best_score:
                best_score = score
                best_title = title
        if best_title and best_score > 0:
            allocation[best_title].append(material)
        else:
            unused.append(material)

    gaps = []
    for title, items in allocation.items():
        if not items:
            gaps.append(
                {
                    "section_title": title,
                    "missing": _missing_material_suggestions(topic, title),
                }
            )

    return {
        "allocation": allocation,
        "unused": unused,
        "gaps": gaps,
        "risk_review": review_interview_material_risks(usable),
    }


def render_interview_material(material: Dict[str, Any]) -> str:
    """将结构化采访素材渲染为稿件可用表达。"""
    label = material.get("speaker_label") or "受访者"
    content = material.get("content", "").strip()
    city = material.get("city")
    project = material.get("project")
    prefix = ""

    if city and project:
        prefix = f"{city}{project}"
    elif city:
        prefix = f"{city}"
    elif project:
        prefix = f"{project}"

    if material.get("quote_style") == "direct" and material.get("can_quote"):
        return f"{prefix}一位{label}表示，\"{content}\""
    if material.get("quote_style") == "background":
        return f"一位熟悉{prefix or '相关情况'}的人士称，{content}"
    return f"{prefix}一位{label}称，{content}"


def review_interview_material_risks(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """检查采访素材使用风险。"""
    risks = []
    for material in materials:
        notes = []
        content = material.get("content", "")
        if material.get("can_quote") and material.get("quote_style") == "direct":
            if not material.get("verification"):
                notes.append("直接引语缺少授权或核验说明")
        if any(keyword in content for keyword in ["保证", "一定", "必然", "内幕", "违规", "造假"]):
            notes.append("存在高风险定性或未经核实表达，建议改为背景材料或删除")
        if any(keyword in content for keyword in ["成交", "认购", "金额", "套", "平方米", "折扣"]):
            if not material.get("verification"):
                notes.append("涉及成交、价格或面积数据，需用公告、网签或机构数据核验")
        if material.get("status") == "background_only" and material.get("can_quote"):
            notes.append("背景材料不应直接引用")
        if material.get("risk_notes"):
            notes.extend(material.get("risk_notes", []))
        if notes:
            risks.append({"material_id": material.get("material_id"), "risks": notes})
    return risks


def build_interview_template(topic_type: str) -> Dict[str, Any]:
    """生成结构化采访记录模板。"""
    if topic_type == "holiday_market":
        return {
            "topic_tags": ["五一", "成交", "来访", "认购", "价格"],
            "roles": ["developer_sales", "broker", "buyer", "developer_marketing"],
            "fields": [
                "城市",
                "项目",
                "采访对象角色",
                "来访变化",
                "认购/成交变化",
                "折扣或优惠",
                "客户结构",
                "客户决策周期",
                "是否可引用",
                "需核验数据",
            ],
            "questions": [
                "假期期间来访量较节前是否有变化？",
                "认购或成交主要集中在哪类房源？",
                "项目是否推出折扣、特价房、渠道政策或金融方案？",
                "客户以刚需、改善还是置换为主？",
                "客户最关注价格、地段、交付还是学区等因素？",
                "成交数据是否可与网签、认购台账或机构数据交叉核验？",
            ],
        }
    if topic_type == "land_market":
        return {
            "topic_tags": ["土地", "城投", "拿地", "土拍", "收储"],
            "roles": ["analyst", "government_staff", "city_investment_staff", "developer_marketing"],
            "fields": ["城市", "地块", "买方", "成交价格", "溢价率", "后续开发安排", "资金来源", "是否可引用"],
            "questions": [
                "该地块买方是否具备实际开发计划？",
                "拿地资金来源是什么？",
                "是否存在合作开发、代建、转让或收储安排？",
                "当地土地市场主要买方结构是否变化？",
            ],
        }
    return {
        "topic_tags": [],
        "roles": INTERVIEW_ROLES,
        "fields": ["城市", "项目/企业", "采访对象角色", "采访内容", "是否可引用", "核验方式"],
        "questions": ["这一变化具体表现是什么？", "是否有数据或文件可以核验？", "是否可以引用？"],
    }


def _build_material_id(date: str, city: Optional[str], project: Optional[str], role: str, content: str) -> str:
    seed = f"{date}-{city or 'na'}-{project or 'na'}-{role}-{content[:20]}"
    safe = "".join(ch if ch.isalnum() else "_" for ch in seed)
    return safe[:80]


def _default_speaker_label(role: str) -> str:
    mapping = {
        "developer_sales": "项目销售人员",
        "developer_marketing": "房企营销人士",
        "buyer": "购房者",
        "homeowner": "业主",
        "broker": "中介经纪人",
        "analyst": "机构分析师",
        "policy_researcher": "政策研究人士",
        "government_staff": "地方政府人士",
        "city_investment_staff": "城投人士",
        "lawyer": "律师",
        "auditor": "审计人士",
    }
    return mapping.get(role, "受访者")


def _topic_score(material: Dict[str, Any], topic: str) -> int:
    score = 0
    text = " ".join(
        [
            " ".join(material.get("topic_tags", [])),
            material.get("content", ""),
            material.get("city", "") or "",
            material.get("project", "") or "",
            material.get("company", "") or "",
        ]
    )
    for keyword in _keywords(topic):
        if keyword and keyword in text:
            score += 2
    return score


def _section_match_score(material: Dict[str, Any], section_title: str) -> int:
    score = 0
    text = " ".join([
        " ".join(material.get("topic_tags", [])),
        material.get("content", ""),
        material.get("role", ""),
    ])
    for keyword in _keywords(section_title):
        if keyword and keyword in text:
            score += 2
    if "成交" in section_title and any(k in text for k in ["认购", "成交", "来访", "去化"]):
        score += 3
    if "项目" in section_title and any(k in text for k in ["项目", "房源", "户型", "折扣"]):
        score += 3
    if "客户" in section_title and any(k in text for k in ["客户", "购房者", "置换", "刚需", "改善"]):
        score += 3
    if "价格" in section_title and any(k in text for k in ["价格", "折扣", "优惠", "特价"]):
        score += 3
    return score


def _missing_material_suggestions(topic: str, section_title: str) -> List[str]:
    suggestions = []
    if "成交" in section_title or "五一" in topic:
        suggestions.extend(["项目销售对来访和认购变化的描述", "机构成交套数/面积数据", "客户现场看房行为"])
    if "项目" in section_title:
        suggestions.extend(["具体项目营销动作", "折扣/特价房源安排", "推盘节奏变化"])
    if "客户" in section_title or "需求" in section_title:
        suggestions.extend(["购房者采访", "中介对客户结构变化的观察", "置换链条案例"])
    if "价格" in section_title or "预期" in section_title:
        suggestions.extend(["价格调整口径", "客户议价情况", "销售对后续优惠持续性的说法"])
    return list(dict.fromkeys(suggestions or ["补充一线采访材料"]))


def _keywords(text: str) -> List[str]:
    common = ["五一", "成交", "来访", "认购", "项目", "客户", "价格", "土地", "城投", "利润", "年报", "政策"]
    return [keyword for keyword in common if keyword in text]
