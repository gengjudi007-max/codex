from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple
from xml.etree import ElementTree

from codex.services.data_fetcher import extract_basic_metrics
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text


LAND_METRIC_FIELDS = {
    "area_sqm",
    "planned_gfa_sqm",
    "land_area_10k_sqm",
    "planned_gfa_10k_sqm",
    "deal_price_wan",
    "starting_price_wan",
    "floor_price_yuan_sqm",
    "land_unit_price_yuan_sqm",
    "equity_ratio",
    "transfer_area",
    "transfer_amount",
    "transacted_area",
    "transaction_unit_price",
    "total_land_count",
    "total_land_amount",
    "total_land_unit_price",
    "city_investment_land_amount",
    "city_investment_amount_share",
    "total_land_gfa",
    "city_investment_land_gfa",
    "city_investment_gfa_share",
    "private_developer_land_amount",
    "central_soe_land_amount",
    "unsold_rate",
    "premium_rate",
    "failed_auction_rate",
    "started_gfa_share",
    "idle_gfa_share",
    "special_bond_land_reserve_amount",
}


def import_terminal_file(path: str, source: str = "terminal") -> Dict[str, Any]:
    """Import CSV/TSV/XLSX exports from data terminals into standard records."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"找不到数据文件：{file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        columns, rows = _read_delimited(file_path, ",")
    elif suffix == ".tsv":
        columns, rows = _read_delimited(file_path, "\t")
    elif suffix == ".xlsx":
        columns, rows = _read_xlsx_first_sheet(file_path)
    else:
        raise ValueError("仅支持 .csv、.tsv、.xlsx 数据文件。")

    records = [
        record
        for row in rows
        if (record := _normalize_record(row, source, file_path.name)) and _is_data_record(record)
    ]
    items = [_record_to_item(record) for record in records]

    return {
        "source": source,
        "file": str(file_path),
        "columns": columns,
        "record_count": len(records),
        "records": records,
        "items": items,
        "city_land_payload": _city_land_payload(records),
    }


def _read_delimited(path: Path, delimiter: str) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = [dict(row) for row in reader]
        return list(reader.fieldnames or []), rows


def _read_xlsx_first_sheet(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_names = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet")]
        if not sheet_names:
            return [], []
        xml = archive.read(sorted(sheet_names)[0])

    root = ElementTree.fromstring(xml)
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: List[List[str]] = []
    for row in root.findall(".//x:sheetData/x:row", namespace):
        values = []
        for cell in row.findall("x:c", namespace):
            values.append(_cell_value(cell, shared_strings, namespace))
        rows.append(values)

    if not rows:
        return [], []
    columns = [normalize_text(value) for value in rows[0]]
    records = []
    for row in rows[1:]:
        record = {column: row[index] if index < len(row) else "" for index, column in enumerate(columns)}
        records.append(record)
    return columns, records


def _read_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    for item in root.findall(".//x:si", namespace):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", namespace)))
    return strings


def _cell_value(cell: ElementTree.Element, shared_strings: List[str], namespace: Dict[str, str]) -> str:
    value = cell.find("x:v", namespace)
    if value is None or value.text is None:
        inline = cell.find(".//x:t", namespace)
        return inline.text if inline is not None and inline.text else ""
    if cell.attrib.get("t") == "s":
        index = int(value.text)
        return shared_strings[index] if index < len(shared_strings) else ""
    return value.text


def _normalize_record(row: Dict[str, Any], source: str, filename: str) -> Dict[str, Any]:
    normalized = {normalize_text(key): normalize_text(value) for key, value in row.items()}
    text = " ".join(value for value in normalized.values() if value)
    return {
        "source": source,
        "source_file": filename,
        "city": normalized.get("city") or normalized.get("城市") or infer_city(text),
        "province": normalized.get("province") or normalized.get("省份"),
        "district": normalized.get("district") or normalized.get("区县"),
        "company": normalized.get("company") or normalized.get("公司") or infer_company(text),
        "bidder": normalized.get("竞得方"),
        "year": normalized.get("year") or normalized.get("年份") or _infer_year(filename),
        "title": normalized.get("title") or normalized.get("标题") or compact_text(text, 80),
        "content": text,
        "raw": normalized,
        "metrics": _extract_record_metrics(normalized, text),
    }


def _is_data_record(record: Dict[str, Any]) -> bool:
    city = normalize_text(record.get("city"))
    province = normalize_text(record.get("province"))
    company = normalize_text(record.get("company"))
    title = normalize_text(record.get("title"))
    metrics = record.get("metrics", {})
    if not (city or province or company) or city.startswith("数据来源") or province.startswith("数据来源"):
        return False
    if title.startswith("指标") or title.startswith("数据来源"):
        return False
    return any(key in metrics for key in LAND_METRIC_FIELDS)


def _infer_year(filename: str) -> str:
    match = re.search(r"(20\d{2})", filename)
    return match.group(1) if match else ""


def _record_to_item(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": record["source"],
        "title": record["title"],
        "summary": record["content"],
        "content": record["content"],
        "city": record.get("city"),
        "province": record.get("province"),
        "district": record.get("district"),
        "company": record.get("company"),
        "bidder": record.get("bidder"),
        "year": record.get("year"),
        "metrics": record["metrics"],
        "source_file": record["source_file"],
    }


def _extract_record_metrics(row: Dict[str, str], text: str) -> Dict[str, Any]:
    metrics = extract_basic_metrics(text)
    for key, value in row.items():
        normalized_key = _metric_key(key)
        if normalized_key and value:
            try:
                metrics[normalized_key] = float(value.replace(",", ""))
            except ValueError:
                metrics[normalized_key] = value
    return metrics


def _metric_key(key: str) -> str:
    aliases = {
        "城市": "city",
        "省份": "province",
        "区县": "district",
        "年份": "year",
        "地块名称": "land_parcel_name",
        "地块编号": "land_parcel_id",
        "宗地名称": "land_parcel_name",
        "宗地编号": "land_parcel_id",
        "规划用途": "land_use",
        "土地用途": "land_use",
        "总用地面积(㎡)": "area_sqm",
        "规划建筑面积(㎡)": "planned_gfa_sqm",
        "土地面积(万㎡)": "land_area_10k_sqm",
        "规划建筑面积(万㎡)": "planned_gfa_10k_sqm",
        "成交价(万元)": "deal_price_wan",
        "拿地总价(万元)": "deal_price_wan",
        "起始价": "starting_price_wan",
        "起始价(万元)": "starting_price_wan",
        "成交楼面价(元/㎡)": "floor_price_yuan_sqm",
        "成交楼面均价": "floor_price_yuan_sqm",
        "成交地面均价": "land_unit_price_yuan_sqm",
        "权益比例(%)": "equity_ratio",
        "成交时间": "transaction_date",
        "拿地时间": "transaction_date",
        "出让日期": "listing_date",
        "出让方式": "listing_method",
        "交易状态": "transaction_status",
        "竞得方": "bidder",
        "成交土地宗数": "total_land_count",
        "成交土地建设用地面积": "total_land_gfa",
        "成交金额": "total_land_amount",
        "土地成交金额": "total_land_amount",
        "成交土地出让金": "total_land_amount",
        "成交土地均价": "total_land_unit_price",
        "成交土地平均溢价率": "premium_rate",
        "城投拿地金额": "city_investment_land_amount",
        "城投拿地占比": "city_investment_amount_share",
        "成交建面": "total_land_gfa",
        "城投拿地建面": "city_investment_land_gfa",
        "民企拿地金额": "private_developer_land_amount",
        "央国企拿地金额": "central_soe_land_amount",
        "溢价率": "premium_rate",
        "溢价率(%)": "premium_rate",
        "平均溢价率": "premium_rate",
        "流拍率": "failed_auction_rate",
        "出让面积": "transfer_area",
        "出让金额": "transfer_amount",
        "成交面积": "transacted_area",
        "成交单价": "transaction_unit_price",
        "开工率": "started_gfa_share",
        "闲置率": "idle_gfa_share",
        "专项债收储金额": "special_bond_land_reserve_amount",
    }
    if key in aliases:
        return aliases[key]
    if key in LAND_METRIC_FIELDS:
        return key
    return ""


def _city_land_payload(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    cities = []
    for record in records:
        metrics = {
            key: value
            for key, value in record.get("metrics", {}).items()
            if key in LAND_METRIC_FIELDS
        }
        if record.get("city") and metrics:
            cities.append(
                {
                    "city": record.get("city"),
                    "year": record.get("year") or "未知年份",
                    "metrics": metrics,
                    "source": record.get("source"),
                    "note": f"导入自 {record.get('source_file')}",
                }
            )
    return {"mode": "city_land_compare", "cities": cities}
