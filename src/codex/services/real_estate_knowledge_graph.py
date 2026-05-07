from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


ENTITY_KEYS = {
    "city": ["city"],
    "buyer": ["buyer", "jdr", "winner", "companyName"],
    "land": ["title", "landName", "zdmc", "xmmc", "name"],
    "policy": ["policy_name", "title"],
}


def build_knowledge_graph(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = {}
    edges = []

    for item in items:
        category = item.get("category") or "unknown"
        raw = item.get("raw") or {}

        city = item.get("city") or raw.get("city")
        title = item.get("title") or raw.get("title")
        buyer = raw.get("buyer") or raw.get("jdr") or raw.get("winner") or raw.get("companyName")

        if city:
            add_node(nodes, f"city:{city}", "city", city)
        if title:
            add_node(nodes, f"item:{title}", category, title)
        if buyer:
            add_node(nodes, f"buyer:{buyer}", "buyer", buyer)

        if city and title:
            edges.append({"source": f"city:{city}", "target": f"item:{title}", "relation": "contains"})
        if buyer and title:
            edges.append({"source": f"buyer:{buyer}", "target": f"item:{title}", "relation": "acquired_or_related"})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }


def add_node(nodes: Dict[str, Dict[str, Any]], node_id: str, node_type: str, label: str) -> None:
    if node_id not in nodes:
        nodes[node_id] = {"id": node_id, "type": node_type, "label": label}


def summarize_graph_by_type(graph: Dict[str, Any]) -> Dict[str, int]:
    counts = defaultdict(int)
    for node in graph.get("nodes", []):
        counts[node.get("type") or "unknown"] += 1
    return dict(counts)
