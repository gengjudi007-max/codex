from __future__ import annotations

from typing import Any, Dict, List

from codex.services.claim_graph import build_claim_graph
from codex.services.propaganda_detector import detect_propaganda_style
from codex.services.risk_chain import analyze_risk_chain
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text

STYLE_PROFILES = {
    "economic_observer": {
        "name": "经济观察报",
        "lead": "以事件、人物或企业动作切入，迅速落到行业周期和公共议题。",
        "structure": "导语 + 三个小标题，强调问题链、行业逻辑和第三方观察。",
        "tone": "冷静、克制、分析性强，避免情绪化和宣传化。",
        "paragraph": "段落中等长度，注意首尾呼应和逻辑递进。",
    },
    "caixin": {
        "name": "财新",
        "lead": "以核心事实、关键数据或政策变化切入，突出证据、因果链和风险边界。",
        "structure": "事实密集、证据先行，强调时间线、责任链和多方信源。",
        "tone": "严谨、压缩、调查性强，避免未经证实的判断。",
        "paragraph": "短段落、强信息密度，关键结论必须有来源支撑。",
    },
}


def build_story_architecture(
    payload: Dict[str, Any],
    style: str = "economic_observer",
) -> Dict[str, Any]:
    selected_style = STYLE_PROFILES.get(style, STYLE_PROFILES["economic_observer"])
    texts = _payload_texts(payload)
    combined = normalize_text(" ".join(texts))
    risk = analyze_risk_chain({"items": [{"summary": text} for text in texts]})
    claim_graph = build_claim_graph(texts, sources=payload.get("sources", []))
    propaganda = detect_propaganda_style(combined)

    return {
        "mode": "story_architecture",
        "style": selected_style,
        "lead_options": _lead_options(combined, risk, selected_style),
        "headline_options": _headline_options(combined, risk, selected_style),
        "section_plan": _section_plan(combined, risk, claim_graph, selected_style),
        "evidence_plan": _evidence_plan(claim_graph),
        "interview_slots": _interview_slots(risk, claim_graph),
        "risk_and_balance": _risk_and_balance(risk, claim_graph, propaganda),
        "style_constraints": _style_constraints(selected_style),
        "do_not_write": [
            "不要虚构采访对象、采访内容和未公开数据。",
            "不要把企业说法写成媒体结论。",
            "不要用绝对化词汇替代证据。",
            "不要在证据不足时给出确定性因果判断。",
        ],
        "claim_boundary": "叙事引擎只生成深度报道结构和写作方案，不自动补造事实、采访或数据。",
    }


def _payload_texts(payload: Dict[str, Any]) -> List[str]:
    if isinstance(payload.get("texts"), list):
        return [normalize_text(text) for text in payload["texts"] if normalize_text(text)]
    if isinstance(payload.get("items"), list):
        texts = []
        for item in payload["items"]:
            if not isinstance(item, dict):
                continue
            texts.append(normalize_text(" ".join(str(item.get(key, "")) for key in ("title", "summary", "content", "text"))))
        return [text for text in texts if text]
    text = normalize_text(payload.get("text") or payload.get("message") or payload.get("content") or "")
    return [text] if text else []


def _lead_options(text: str, risk: Dict[str, Any], style: Dict[str, str]) -> List[Dict[str, str]]:
    city = infer_city(text) or "相关城市"
    company = infer_company(text) or "相关企业"
    risk_summary = risk.get("risk_map", {}).get("summary") or "行业变化"
    return [
        {
            "type": "事件切入",
            "suggestion": f"从{city}或{company}的最新动作切入，引出{risk_summary}。",
            "fit": style["name"],
        },
        {
            "type": "数据切入",
            "suggestion": "以最关键的财务、土地或政策数据开篇，随后解释其背后的行业周期变化。",
            "fit": "财新" if style["name"] == "财新" else "经济观察报",
        },
        {
            "type": "问题切入",
            "suggestion": "先提出一个行业问题，再用企业案例、政策变化和风险链逐步回答。",
            "fit": "经济观察报",
        },
    ]


def _headline_options(text: str, risk: Dict[str, Any], style: Dict[str, str]) -> List[str]:
    city = infer_city(text)
    company = infer_company(text)
    risk_nodes = risk.get("risk_map", {}).get("nodes", [])
    core = risk_nodes[0] if risk_nodes else "房地产新周期"
    subject = city or company or "房地产行业"
    if style["name"] == "财新":
        return [
            f"{subject}{core}追踪",
            f"{subject}风险链待解",
            f"{subject}调整背后的证据链",
        ]
    return [
        f"{subject}进入新一轮调整",
        f"{core}下的{subject}样本",
        f"周期退潮后的{subject}再观察",
    ]


def _section_plan(
    text: str,
    risk: Dict[str, Any],
    claim_graph: Dict[str, Any],
    style: Dict[str, str],
) -> List[Dict[str, Any]]:
    return [
        {
            "title": "事实发生了什么",
            "purpose": "交代新闻由头、核心事实、主体动作和时间线。",
            "writing_notes": [
                "先写可核验事实，再写企业或地方口径。",
                "关键数字必须标明来源。",
                "避免用企业愿景替代新闻由头。",
            ],
            "evidence_needed": _top_claim_actions(claim_graph),
        },
        {
            "title": "为什么此时发生",
            "purpose": "解释行业周期、政策语义、财务约束和风险链。",
            "writing_notes": [
                "把单个事件放入房地产下行、土地财政、融资收缩或物业周期中解释。",
                "区分直接原因、背景原因和待核验推断。",
                "需要加入第三方信源或反向信息。",
            ],
            "risk_nodes": risk.get("risk_map", {}).get("nodes", []),
        },
        {
            "title": "影响与未解问题",
            "purpose": "分析对企业、城市、行业和购房者/业主的影响，并列出后续观察。",
            "writing_notes": [
                "不要把趋势写满，保留不确定性。",
                "写出后续跟踪指标。",
                "把采访缺口和事实核验缺口列入结尾。",
            ],
            "open_questions": risk.get("reporting_path", []),
        },
    ]


def _evidence_plan(claim_graph: Dict[str, Any]) -> Dict[str, Any]:
    verification = []
    for node in claim_graph.get("nodes", []):
        if node.get("type") == "verification_action":
            verification.append({"action": node.get("label"), "metadata": node.get("metadata", {})})
    return {
        "claim_count": sum(1 for node in claim_graph.get("nodes", []) if node.get("type") == "claim"),
        "source_count": sum(1 for node in claim_graph.get("nodes", []) if node.get("type") == "source"),
        "contradiction_count": claim_graph.get("contradictions", {}).get("contradiction_count", 0),
        "verification_actions": verification[:10],
    }


def _interview_slots(risk: Dict[str, Any], claim_graph: Dict[str, Any]) -> List[Dict[str, str]]:
    slots = [
        {"role": "政策/行业研究人士", "purpose": "解释政策语义和行业周期变化。"},
        {"role": "企业或项目相关人士", "purpose": "核实主体动作、资金来源、项目状态和经营压力。"},
        {"role": "第三方机构或投资人士", "purpose": "提供财务、市场和风险交叉判断。"},
    ]
    if risk.get("chains"):
        slots.append({"role": "地方政府/城投/金融机构相关人士", "purpose": "核验土地、专项债、收储和融资安排。"})
    if claim_graph.get("contradictions", {}).get("contradiction_count", 0):
        slots.append({"role": "原始数据或文件提供方", "purpose": "解释数字、时间或口径冲突。"})
    return slots


def _risk_and_balance(
    risk: Dict[str, Any],
    claim_graph: Dict[str, Any],
    propaganda: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "risk_nodes": risk.get("risk_map", {}).get("nodes", []),
        "contradictions": claim_graph.get("contradictions", {}).get("contradictions", []),
        "propaganda_risk": propaganda.get("risk_level"),
        "balance_requirements": [
            "至少加入一个非企业口径信源。",
            "对所有强判断补充证据或改为待核验表述。",
            "对风险链写清楚已发生、正在累积和可能发生的边界。",
        ],
    }


def _style_constraints(style: Dict[str, str]) -> List[str]:
    return [
        style["lead"],
        style["structure"],
        style["tone"],
        style["paragraph"],
        "使用第三方新闻视角，不使用企业第一人称。",
        "事实、判断、采访说法分层呈现。",
    ]


def _top_claim_actions(claim_graph: Dict[str, Any]) -> List[str]:
    actions = []
    for node in claim_graph.get("nodes", []):
        if node.get("type") == "verification_action":
            actions.append(str(node.get("label")))
    return actions[:5]
