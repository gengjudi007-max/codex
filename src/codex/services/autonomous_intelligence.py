from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from typing import Any, Dict, List

from codex.services.knowledge_graph_store import rebuild_knowledge_graph, related_entities
from codex.services.retrieval_engine import alerts_query, claims_query, entity_query, newsroom_summary
from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db

HIGH_RISK_CLAIM_STATUSES = {"unsupported", "needs_verification", "attribution_required"}
WATCH_RISK_TERMS = ["土地财政压力", "城投托底", "应收账款", "减值", "经营现金流", "库存去化", "债务重组", "退出低效项目"]


def run_autonomous_intelligence(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Run proactive newsroom intelligence discovery over persisted knowledge."""
    init_db(db_path)
    kg = rebuild_knowledge_graph(db_path)
    anomalies = detect_anomalies(db_path)
    trends = detect_trends(db_path)
    relationships = discover_relationships(db_path)
    contradictions = track_contradiction_evolution(db_path)
    suggestions = generate_investigation_suggestions(anomalies, trends, relationships, contradictions)
    return {
        "mode": "autonomous_intelligence",
        "db_path": db_path,
        "knowledge_graph": kg.get("summary", {}),
        "anomalies": anomalies,
        "trends": trends,
        "relationships": relationships,
        "contradiction_evolution": contradictions,
        "investigation_suggestions": suggestions,
        "early_warnings": _early_warnings(anomalies, trends, contradictions),
        "claim_boundary": "自主情报层只生成异常、趋势和调查假设，不自动认定事实结论。",
    }


def detect_anomalies(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    summary = newsroom_summary(db_path)
    alerts = alerts_query(db_path, limit=100).get("alerts", [])
    high_risk_claims = []
    for status in HIGH_RISK_CLAIM_STATUSES:
        high_risk_claims.extend(claims_query(status=status, db_path=db_path, limit=50).get("claims", []))

    anomalies: List[Dict[str, Any]] = []
    if len(alerts) >= 3:
        anomalies.append({"type": "alert_cluster", "severity": "medium", "count": len(alerts), "reason": "近期警报累计较多，需要复盘是否形成持续信号。"})
    if high_risk_claims:
        anomalies.append({"type": "fact_check_risk", "severity": "high", "count": len(high_risk_claims), "reason": "存在未核验或需归属的高风险声明。"})
    if not summary.get("source_types"):
        anomalies.append({"type": "empty_source_base", "severity": "high", "reason": "数据库尚无有效信源，无法形成稳定编辑部运转。"})
    return anomalies


def detect_trends(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    trends: List[Dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT risks_json, risk_chains_json, city, company FROM memory_events").fetchall()
    risk_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    company_counter: Counter[str] = Counter()
    for row in rows:
        risk_counter.update(_json_list(row["risks_json"]))
        if row["city"]:
            city_counter[row["city"]] += 1
        if row["company"]:
            company_counter[row["company"]] += 1
    for risk, count in risk_counter.most_common(10):
        if count >= 2 or risk in WATCH_RISK_TERMS:
            trends.append({"type": "risk_frequency", "risk": risk, "count": count, "severity": "high" if count >= 3 else "medium"})
    for city, count in city_counter.most_common(10):
        if count >= 2:
            trends.append({"type": "city_attention", "city": city, "count": count, "severity": "medium"})
    for company, count in company_counter.most_common(10):
        if count >= 2:
            trends.append({"type": "company_attention", "company": company, "count": count, "severity": "medium"})
    return trends


def discover_relationships(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    relationships: List[Dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        edges = conn.execute("SELECT source_id, target_id, relation, weight FROM kg_edges ORDER BY weight DESC LIMIT 100").fetchall()
    for edge in edges:
        if edge["weight"] >= 2:
            relationships.append({"type": "repeated_relation", "source_id": edge["source_id"], "target_id": edge["target_id"], "relation": edge["relation"], "weight": edge["weight"]})
    for term in WATCH_RISK_TERMS:
        rel = related_entities(term, db_path=db_path, limit=10)
        if rel.get("related_count", 0) > 0:
            relationships.append({"type": "risk_relation", "risk": term, "related_count": rel.get("related_count"), "sample": rel.get("relations", [])[:3]})
    return relationships[:30]


def track_contradiction_evolution(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    high_risk = []
    for status in HIGH_RISK_CLAIM_STATUSES:
        high_risk.extend(claims_query(status=status, db_path=db_path, limit=100).get("claims", []))
    by_status = Counter(claim.get("status") for claim in high_risk)
    return {
        "high_risk_claim_count": len(high_risk),
        "by_status": dict(by_status),
        "sample_claims": high_risk[:10],
        "reading": "高风险声明越多，越需要先做事实核查和来源补强，而不是推进终稿。" if high_risk else "暂未发现明显声明风险。",
    }


def generate_investigation_suggestions(
    anomalies: List[Dict[str, Any]],
    trends: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    contradictions: Dict[str, Any],
) -> List[Dict[str, Any]]:
    suggestions: List[Dict[str, Any]] = []
    if any(item.get("type") == "empty_source_base" for item in anomalies):
        suggestions.append({"priority": "high", "topic": "补齐基础数据源", "action": "先接入公告、土地、专项债和年报来源，否则自动情报无法稳定运转。"})
    if contradictions.get("high_risk_claim_count", 0):
        suggestions.append({"priority": "high", "topic": "事实核查优先", "action": "优先处理 unsupported / needs_verification / attribution_required 声明。"})
    for trend in trends[:5]:
        if trend.get("type") == "risk_frequency":
            suggestions.append({"priority": trend.get("severity", "medium"), "topic": f"追踪风险：{trend.get('risk')}", "action": "检索相关城市、企业和事件，形成风险演化时间线。"})
        elif trend.get("type") == "city_attention":
            suggestions.append({"priority": "medium", "topic": f"城市跟踪：{trend.get('city')}", "action": "整理该城市近期土地、政策、库存和房企动作。"})
        elif trend.get("type") == "company_attention":
            suggestions.append({"priority": "medium", "topic": f"企业跟踪：{trend.get('company')}", "action": "整理该企业财报、融资、投资和项目风险。"})
    if relationships:
        suggestions.append({"priority": "medium", "topic": "关系图谱复盘", "action": "检查高频关系是否指向新的调查链条或长期观察对象。"})
    return suggestions or [{"priority": "low", "topic": "继续监控", "action": "当前未发现强信号，保持数据源更新。"}]


def _early_warnings(anomalies: List[Dict[str, Any]], trends: List[Dict[str, Any]], contradictions: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    if any(item.get("severity") == "high" for item in anomalies):
        warnings.append("存在高风险系统或事实核查异常。")
    if any(item.get("severity") == "high" for item in trends):
        warnings.append("存在高频风险信号，建议进入专题跟踪。")
    if contradictions.get("high_risk_claim_count", 0) >= 3:
        warnings.append("高风险声明累计较多，终稿发布前必须集中核验。")
    return warnings or ["暂无强预警信号。"]


def _json_list(value: str | None) -> List[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
