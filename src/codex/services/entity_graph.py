from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from codex.services.memory_graph import DEFAULT_MEMORY_PATH, iter_memory
from codex.services.text_utils import unique


def build_entity_graph(path: str = DEFAULT_MEMORY_PATH, min_weight: int = 1) -> Dict[str, Any]:
    """Build a lightweight graph from remembered events.

    Nodes are cities, companies, risks, risk chains, and events.
    Edges are co-occurrences inside the same remembered event.
    """
    events = list(iter_memory(path))
    node_map: Dict[str, Dict[str, Any]] = {}
    edge_weights: Counter[Tuple[str, str, str]] = Counter()

    for event in events:
        event_id = str(event.get("id") or event.get("title"))
        _add_node(node_map, event_id, "event", event.get("title") or event_id)

        entities = _event_entities(event)
        for entity_id, entity_type, label in entities:
            _add_node(node_map, entity_id, entity_type, label)
            _add_edge(edge_weights, event_id, entity_id, "mentions")

        for left_index, left in enumerate(entities):
            for right in entities[left_index + 1 :]:
                relation = _relation_type(left[1], right[1])
                _add_edge(edge_weights, left[0], right[0], relation)

    edges = [
        {"source": source, "target": target, "relation": relation, "weight": weight}
        for (source, target, relation), weight in edge_weights.items()
        if weight >= min_weight
    ]

    return {
        "path": path,
        "node_count": len(node_map),
        "edge_count": len(edges),
        "nodes": sorted(node_map.values(), key=lambda node: (node["type"], node["label"])),
        "edges": sorted(edges, key=lambda edge: edge["weight"], reverse=True),
    }


def entity_profile(entity: str, path: str = DEFAULT_MEMORY_PATH) -> Dict[str, Any]:
    events = [event for event in iter_memory(path) if _event_contains_entity(event, entity)]
    risks = []
    chains = []
    cities = []
    companies = []
    for event in events:
        risks.extend(event.get("risks", []))
        chains.extend(event.get("risk_chains", []))
        if event.get("city"):
            cities.append(event["city"])
        if event.get("company"):
            companies.append(event["company"])

    return {
        "entity": entity,
        "event_count": len(events),
        "cities": unique(cities),
        "companies": unique(companies),
        "risks": unique(risks),
        "risk_chains": unique(chains),
        "recent_events": sorted(
            [
                {
                    "occurred_at": event.get("occurred_at"),
                    "title": event.get("title"),
                    "summary": event.get("summary"),
                    "risks": event.get("risks", []),
                    "risk_chains": event.get("risk_chains", []),
                }
                for event in events
            ],
            key=lambda item: str(item.get("occurred_at") or ""),
            reverse=True,
        )[:10],
    }


def graph_summary(path: str = DEFAULT_MEMORY_PATH) -> Dict[str, Any]:
    graph = build_entity_graph(path)
    type_counts: Dict[str, int] = defaultdict(int)
    for node in graph["nodes"]:
        type_counts[node["type"]] += 1
    return {
        "path": path,
        "node_count": graph["node_count"],
        "edge_count": graph["edge_count"],
        "node_type_counts": dict(type_counts),
        "top_edges": graph["edges"][:10],
    }


def _event_entities(event: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    entities: List[Tuple[str, str, str]] = []
    if event.get("city"):
        entities.append((f"city:{event['city']}", "city", str(event["city"])))
    if event.get("company"):
        entities.append((f"company:{event['company']}", "company", str(event["company"])))
    for risk in event.get("risks", []):
        entities.append((f"risk:{risk}", "risk", str(risk)))
    for chain in event.get("risk_chains", []):
        entities.append((f"chain:{chain}", "risk_chain", str(chain)))
    for entity in event.get("entities", []):
        if entity and not any(existing[2] == entity for existing in entities):
            entities.append((f"entity:{entity}", "entity", str(entity)))
    return entities


def _add_node(node_map: Dict[str, Dict[str, Any]], node_id: str, node_type: str, label: str) -> None:
    if node_id not in node_map:
        node_map[node_id] = {"id": node_id, "type": node_type, "label": label}


def _add_edge(edge_weights: Counter[Tuple[str, str, str]], source: str, target: str, relation: str) -> None:
    if source == target:
        return
    ordered = tuple(sorted([source, target]))
    edge_weights[(ordered[0], ordered[1], relation)] += 1


def _relation_type(left_type: str, right_type: str) -> str:
    types = {left_type, right_type}
    if "city" in types and "risk" in types:
        return "city_risk"
    if "company" in types and "risk" in types:
        return "company_risk"
    if "risk" in types and "risk_chain" in types:
        return "risk_chain_signal"
    return "co_occurs"


def _event_contains_entity(event: Dict[str, Any], entity: str) -> bool:
    values: List[str] = []
    for key in ("title", "summary", "content", "city", "company"):
        if event.get(key):
            values.append(str(event[key]))
    values.extend(str(value) for value in event.get("entities", []))
    values.extend(str(value) for value in event.get("risks", []))
    values.extend(str(value) for value in event.get("risk_chains", []))
    return entity in " ".join(values)
