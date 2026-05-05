from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from codex.config import Config
from codex.services.evidence import source_quality
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text


class IFIndError(RuntimeError):
    pass


@dataclass
class IFIndQuery:
    function: str
    codes: str
    indicators: str = ""
    params: str = ""
    start_date: str = ""
    end_date: str = ""
    source: str = "同花顺iFinD"


class IFIndClient:
    """Optional adapter for 同花顺 iFinD Python SDK.

    The project intentionally does not depend on iFinD at install time. Install the
    vendor SDK locally and provide credentials through IFIND_USER/IFIND_PASSWORD.
    """

    def __init__(self, sdk: Optional[Any] = None, config: Optional[Config] = None) -> None:
        self.sdk = sdk or _load_sdk()
        self.config = config or Config.from_env()

    def query(self, query: IFIndQuery) -> Dict[str, Any]:
        self._login_if_configured()
        try:
            raw = self._call(query)
            return _normalize_result(raw, query)
        finally:
            self._logout_if_available()

    def _login_if_configured(self) -> None:
        login = getattr(self.sdk, "THS_iFinDLogin", None)
        if not login:
            return
        if not self.config.ifind_user or not self.config.ifind_password:
            return
        result = login(self.config.ifind_user, self.config.ifind_password)
        error_code = _error_code(result)
        if error_code not in {None, 0, "0"}:
            raise IFIndError(f"iFinD 登录失败：{_error_message(result)}")

    def _logout_if_available(self) -> None:
        logout = getattr(self.sdk, "THS_iFinDLogout", None)
        if logout:
            logout()

    def _call(self, query: IFIndQuery) -> Any:
        function = query.function.lower()
        if function in {"hq", "ths_hq"}:
            return self.sdk.THS_HQ(query.codes, query.indicators, query.params)
        if function in {"ds", "ths_ds"}:
            return self.sdk.THS_DS(
                query.codes,
                query.indicators,
                query.params,
                query.start_date,
                query.end_date,
            )
        if function in {"edb", "ths_edb"}:
            return self.sdk.THS_EDB(query.codes, query.params, query.start_date, query.end_date)
        if function in {"bd", "ths_bd"}:
            return self.sdk.THS_BD(query.codes, query.indicators, query.params)
        raise IFIndError(f"暂不支持的 iFinD 函数：{query.function}")


def run_ifind_query(payload: Dict[str, Any], sdk: Optional[Any] = None) -> Dict[str, Any]:
    query = IFIndQuery(
        function=str(payload.get("function") or payload.get("api") or ""),
        codes=str(payload.get("codes") or payload.get("code") or ""),
        indicators=str(payload.get("indicators") or payload.get("indicator") or ""),
        params=str(payload.get("params") or ""),
        start_date=str(payload.get("start_date") or payload.get("start") or ""),
        end_date=str(payload.get("end_date") or payload.get("end") or ""),
        source=str(payload.get("source") or "同花顺iFinD"),
    )
    if not query.function or not query.codes:
        raise IFIndError("iFinD 查询需要 function 和 codes。")
    return IFIndClient(sdk=sdk).query(query)


def ifind_result_to_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    rows = result.get("rows", [])
    for row in rows:
        text = " ".join(str(value) for value in row.values() if value not in {None, ""})
        items.append(
            {
                "source": result.get("source", "同花顺iFinD"),
                "title": compact_text(text, 80) or result.get("query", {}).get("codes", "iFinD数据"),
                "summary": text,
                "content": text,
                "city": infer_city(text),
                "company": infer_company(text),
                "metrics": _metrics_from_row(row),
                "source_quality": source_quality("", "同花顺iFinD"),
                "status": "ok",
            }
        )
    return items


def _load_sdk() -> Any:
    try:
        return importlib.import_module("iFinDPy")
    except ImportError as exc:
        raise IFIndError(
            "未检测到同花顺 iFinD Python SDK。请先安装/配置 iFinDPy，并设置 IFIND_USER、IFIND_PASSWORD。"
        ) from exc


def _normalize_result(raw: Any, query: IFIndQuery) -> Dict[str, Any]:
    error_code = _error_code(raw)
    if error_code not in {None, 0, "0"}:
        raise IFIndError(f"iFinD 查询失败：{_error_message(raw)}")

    rows = _rows(raw)
    return {
        "source": query.source,
        "query": {
            "function": query.function,
            "codes": query.codes,
            "indicators": query.indicators,
            "params": query.params,
            "start_date": query.start_date,
            "end_date": query.end_date,
        },
        "row_count": len(rows),
        "rows": rows,
        "raw_type": type(raw).__name__,
    }


def _error_code(raw: Any) -> Any:
    if isinstance(raw, dict):
        return raw.get("errorcode") or raw.get("error_code") or raw.get("ErrorCode")
    return (
        getattr(raw, "errorcode", None)
        or getattr(raw, "error_code", None)
        or getattr(raw, "ErrorCode", None)
    )


def _error_message(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("errormsg") or raw.get("message") or raw)
    return str(getattr(raw, "errormsg", None) or getattr(raw, "message", None) or raw)


def _rows(raw: Any) -> List[Dict[str, Any]]:
    data = raw.get("data") if isinstance(raw, dict) else getattr(raw, "data", raw)
    if data is None:
        return []
    if hasattr(data, "to_dict"):
        records = data.to_dict(orient="records")
        return [_clean_row(record) for record in records]
    if isinstance(data, list):
        if not data:
            return []
        if all(isinstance(item, dict) for item in data):
            return [_clean_row(item) for item in data]
        return [{"value": item} for item in data]
    if isinstance(data, dict):
        if all(isinstance(value, list) for value in data.values()):
            keys = list(data.keys())
            length = max(len(value) for value in data.values()) if data else 0
            rows = []
            for index in range(length):
                rows.append(
                    {
                        key: data[key][index] if index < len(data[key]) else None
                        for key in keys
                    }
                )
            return [_clean_row(row) for row in rows]
        return [_clean_row(data)]
    return [{"value": data}]


def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {normalize_text(key): value for key, value in row.items()}


def _metrics_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (int, float)):
            metrics[key] = value
        elif isinstance(value, str):
            try:
                metrics[key] = float(value.replace(",", ""))
            except ValueError:
                continue
    return metrics
