from __future__ import annotations

from typing import Any, Dict, List

from codex.services.evidence import build_evidence, assess_confidence
from codex.services.text_utils import compact_text, infer_city, infer_company, unique


DOMAIN_KEYWORDS = {
    "政策": ["政策", "住建", "央行", "金融监管", "因城施策", "止跌回稳", "保障房", "房地产税"],
    "市场": ["成交", "房价", "库存", "去化", "二手房", "新房", "挂牌", "溢价率"],
    "企业": ["公告", "年报", "净利润", "亏损", "减值", "债务", "销售额", "现金流"],
    "土地": ["土地", "土拍", "供地", "拿地", "流拍", "底价成交", "城投", "土地财政"],
    "金融": ["REITs", "ABS", "CMBS", "经营性物业贷", "白名单", "展期", "融资"],
    "城市更新": ["城市更新", "城中村", "老旧小区", "收储", "安置", "低效用地"],
}

SIGNAL_KEYWORDS = {
    "异常变化": ["大幅", "骤降", "骤增", "首次", "罕见", "创下", "超过", "低于", "连续"],
    "趋势拐点": ["回升", "转正", "收窄", "扩大", "见底", "反弹", "转弱", "改善"],
    "风险暴露": ["逾期", "违约", "停工", "流动性", "亏损", "减值", "闲置", "去化压力"],
    "政策边际变化": ["调整", "放松", "收紧", "优化", "新政", "试点", "取消", "降低"],
    "主体动作": ["收购", "出售", "重组", "并购", "拿地", "退出", "发行", "增持"],
}


def monitor_signals(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """从连续信息流中归纳行业变化信号和跟踪队列。"""
    normalized = [_normalize_item(item) for item in items if isinstance(item, dict)]
    signals = [_build_signal(item) for item in normalized]
    ranked = sorted(signals, key=lambda signal: signal["urgency_score"], reverse=True)

    return {
        "input_count": len(items),
        "valid_count": len(normalized),
        "signals": ranked,
        "domain_summary": _domain_summary(ranked),
        "watchlist": _watchlist(ranked),
        "next_actions": _next_actions(ranked),
        "warnings": _warnings(items, normalized, ranked),
    }


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "content"))
    normalized = dict(item)
    normalized["text"] = text
    normalized.setdefault("title", compact_text(text, 60) or "未命名信息")
    normalized.setdefault("city", infer_city(text))
    normalized.setdefault("company", infer_company(text))
    return normalized


def _build_signal(item: Dict[str, Any]) -> Dict[str, Any]:
    text = item.get("text", "")
    domains = _matched_groups(text, DOMAIN_KEYWORDS) or ["综合"]
    signal_types = _matched_groups(text, SIGNAL_KEYWORDS) or ["常规动态"]
    urgency_score = _urgency_score(text, domains, signal_types)
    evidence = build_evidence(item)
    credibility = assess_confidence(
        evidence,
        has_metrics=any(keyword in text for keyword in ["超过", "%", "亿元", "万平方米", "同比"]),
        has_original_url=bool(item.get("url") or item.get("source_url")),
    )

    return {
        "title": item.get("title", "未命名信息"),
        "source": item.get("source", "unknown"),
        "city": item.get("city"),
        "company": item.get("company"),
        "domains": domains,
        "signal_types": signal_types,
        "urgency_score": urgency_score,
        "priority": _priority(urgency_score),
        "why_it_matters": _why_it_matters(domains, signal_types),
        "follow_up_questions": _follow_up_questions(domains, signal_types),
        "evidence": evidence,
        **credibility,
    }


def _matched_groups(text: str, mapping: Dict[str, List[str]]) -> List[str]:
    return [name for name, keywords in mapping.items() if any(keyword in text for keyword in keywords)]


def _urgency_score(text: str, domains: List[str], signal_types: List[str]) -> int:
    score = 45
    score += min(len(domains), 3) * 8
    score += min(len(signal_types), 3) * 10
    if any(keyword in text for keyword in ["超过", "%", "亿元", "万平方米", "同比"]):
        score += 10
    if any(signal in signal_types for signal in ["异常变化", "风险暴露", "政策边际变化"]):
        score += 12
    return min(score, 100)


def _priority(score: int) -> str:
    if score >= 85:
        return "立即核验"
    if score >= 70:
        return "进入选题池"
    return "持续观察"


def _why_it_matters(domains: List[str], signal_types: List[str]) -> str:
    domain_text = "、".join(domains)
    signal_text = "、".join(signal_types)
    return f"该信息同时指向{domain_text}领域的{signal_text}，可能形成报道线索或后续跟踪指标。"


def _follow_up_questions(domains: List[str], signal_types: List[str]) -> List[str]:
    questions = ["原始出处、发布时间和统计口径是什么？", "是否有历史同期或同城可比样本？"]
    if "土地" in domains:
        questions.append("买方结构、溢价率和后续开工状态是否支持市场修复判断？")
    if "企业" in domains:
        questions.append("企业动作会如何影响利润、现金流、债务期限和项目交付？")
    if "政策" in domains:
        questions.append("地方执行细则和金融机构落地节奏是否已经出现变化？")
    if "风险暴露" in signal_types:
        questions.append("是否存在需要给当事方回应机会的重大风险事实？")
    return unique(questions)


def _domain_summary(signals: List[Dict[str, Any]]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for signal in signals:
        for domain in signal["domains"]:
            summary[domain] = summary.get(domain, 0) + 1
    return dict(sorted(summary.items(), key=lambda item: item[1], reverse=True))


def _watchlist(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "title": signal["title"],
            "priority": signal["priority"],
            "entities": unique([signal.get("city") or "", signal.get("company") or ""]),
            "next_check": signal["follow_up_questions"][0],
        }
        for signal in signals[:5]
    ]


def _next_actions(signals: List[Dict[str, Any]]) -> List[str]:
    if not signals:
        return ["补充至少一条政策、公告、土地、金融或市场数据。"]
    return [
        "先核验优先级最高线索的原文和关键数字口径。",
        "把同领域信号按城市、企业和时间排序，寻找连续变化而非孤立事件。",
        "对进入选题池的线索补充采访对象、材料清单和摄影现场。",
    ]


def _warnings(
    original_items: List[Any],
    normalized_items: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
) -> List[str]:
    warnings = []
    if len(original_items) != len(normalized_items):
        warnings.append(f"已忽略 {len(original_items) - len(normalized_items)} 条非对象输入。")
    if normalized_items and not signals:
        warnings.append("暂未识别出明确变化信号。")
    return warnings
