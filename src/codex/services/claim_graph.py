from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from codex.services.contradiction_engine import detect_contradictions
from codex.services.fact_check_engine import run_fact_check
from codex.services.text_utils import compact_text, normalize_text


def build_claim_graph(texts: List[Any], sources: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Build a traceable graph connecting claims, evidence, sources, and contradictions."""
    source_list = sources or []
    fact_checks = []
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    for index, text in enumerate(texts):
        document = _document(index, text)
        _add_node(nodes, document["id"], "document", document["title"], {"text": document["text"]})
        check = run_fact_check(document["text"], sources=source_list)
        fact_checks.append({"document": document, "fact_check": check})

        for claim_index, claim in enumerate(check["claims"]):
            claim_id = _claim_id(document["id"], claim_index, claim["text"])
            _add_node(
                nodes,
                claim_id,
                "claim",
                compact_text(claim["text"], 80),
                {
                    "claim_type": claim["type"],
                    "risk_flags": claim.get("risk_flags", []),
                    "numbers": claim.get("numbers", []),
                    "dates": claim.get("dates", []),
                },
            )
            edges.append({"source": document["id"], "target": claim_id, "relation": "contains_claim"})

        for ledger_index, ledger in enumerate(check["evidence_ledger"]):
            claim_id = _claim_id(document["id"], ledger_index, ledger["claim"])
            for source in ledger.get("matched_sources", []):
                source_id = _source_id(source)
                _add_node(
                    nodes,
                    source_id,
                    "source",
                    str(source.get("title") or source.get("source_type") or "source"),
                    {
                        "source_type": source.get("source_type"),
                        "credibility_score": source.get("credibility_score"),
                        "url": source.get("url"),
                    },
                )
                edges.append(
                    {
                        "source": source_id,
                        "target": claim_id,
                        "relation": "supports",
                        "weight": source.get("credibility_score", 0),
                        "match_score": source.get("match_score", 0),
                    }
                )

    contradictions = detect_contradictions(texts, sources=source_list)
    for index, contradiction in enumerate(contradictions.get("contradictions", [])):
        contradiction_id = f"contradiction:{index}:{_hash(str(contradiction))}"
        _add_node(
            nodes,
            contradiction_id,
            "contradiction",
            contradiction.get("type", "contradiction"),
            contradiction,
        )
        for claim in contradiction.get("claims", []):
            for node_id, node in nodes.items():
                if node["type"] == "claim" and claim.get("claim") in node.get("metadata", {}).get("text", ""):
                    edges.append({"source": contradiction_id, "target": node_id, "relation": "flags"})

    verification_nodes = _verification_nodes(fact_checks)
    for node in verification_nodes:
        _add_node(nodes, node["id"], "verification_action", node["label"], node["metadata"])
        edges.append({"source": node["claim_id"], "target": node["id"], "relation": "requires_action"})

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
        "fact_checks": fact_checks,
        "contradictions": contradictions,
        "claim_boundary": "声明图谱展示证据关系和核验状态，不自动判断事实真伪；最终仍需核对原始材料。",
    }


def _document(index: int, text: Any) -> Dict[str, str]:
    if isinstance(text, dict):
        body = normalize_text(" ".join(str(text.get(key, "")) for key in ("title", "summary", "content", "text")))
        return {
            "id": str(text.get("id") or f"document:{index}"),
            "title": str(text.get("title") or f"document_{index}"),
            "text": body,
        }
    body = normalize_text(text)
    return {"id": f"document:{index}", "title": f"document_{index}", "text": body}


def _add_node(
    nodes: Dict[str, Dict[str, Any]],
    node_id: str,
    node_type: str,
    label: str,
    metadata: Dict[str, Any] | None = None,
) -> None:
    if node_id not in nodes:
        node_metadata = dict(metadata or {})
        nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "metadata": node_metadata,
        }
    elif metadata:
        nodes[node_id]["metadata"].update(metadata)


def _claim_id(document_id: str, index: int, text: str) -> str:
    return f"claim:{document_id}:{index}:{_hash(text)}"


def _source_id(source: Dict[str, Any]) -> str:
    basis = "|".join(str(source.get(key, "")) for key in ("title", "source_type", "url", "text"))
    return f"source:{_hash(basis)}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _verification_nodes(fact_checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes = []
    for item in fact_checks:
        document_id = item["document"]["id"]
        verification_results = item["fact_check"]["verification"]["results"]
        for index, result in enumerate(verification_results):
            claim_id = _claim_id(document_id, index, result["claim"])
            action_id = f"action:{claim_id}"
            nodes.append(
                {
                    "id": action_id,
                    "claim_id": claim_id,
                    "label": result.get("required_action", "核验该声明。"),
                    "metadata": {
                        "status": result.get("status"),
                        "risk_flags": result.get("risk_flags", []),
                        "best_source_score": result.get("best_source_score"),
                    },
                }
            )
    return nodes
