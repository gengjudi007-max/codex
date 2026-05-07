from __future__ import annotations

from typing import Any, Dict

from codex.interaction_core.defaults import error_response
from codex.interaction_core.handlers import dispatch
from codex.interaction_core.pipeline import run_topic_pipeline
from codex.interaction_core.router import infer_mode


def analyze_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route structured or free-text input to the matching reporting model."""
    if not isinstance(payload, dict):
        return error_response("payload 必须是 JSON 对象。")

    mode = infer_mode(payload)
    return dispatch(mode, payload)
