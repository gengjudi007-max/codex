from typing import Any, Dict, List, Optional


IMPORTANT_METRICS = [
    "revenue_yoy",
    "net_profit_yoy",
    "gross_margin",
    "impairment_loss",
    "operating_cash_flow",
    "interest_bearing_debt",
    "cash_short_debt_ratio",
    "contracted_sales_yoy",
]


def parse_annual_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """解析房企年报关键指标，并输出可供选题规则系统识别的结构化信息。

    当前版本接收已经结构化的年报摘要数据。后续可以继续扩展为：
    1. 从 PDF/HTML 年报中抽取文本；
    2. 自动识别财务表格；
    3. 与上年数据和同业数据进行横向比较。
    """
    company = report.get("company", "未知房企")
    year = report.get("year", "未知年份")
    metrics = report.get("metrics", {})

    signals = _detect_report_signals(metrics)
    summary_parts = [f"{company}{year}年报"]
    summary_parts.extend(signal["description"] for signal in signals)

    return {
        "source": "annual_report",
        "company": company,
        "title": f"{company}{year}年报解析",
        "summary": "；".join(summary_parts),
        "content": "；".join(summary_parts),
        "year": year,
        "metrics": metrics,
        "signals": signals,
        "keywords": [signal["keyword"] for signal in signals],
    }


def parse_annual_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """批量解析房企年报。"""
    return [parse_annual_report(report) for report in reports]


def _detect_report_signals(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    signals: List[Dict[str, str]] = []

    revenue_yoy = _as_float(metrics.get("revenue_yoy"))
    if revenue_yoy is not None and revenue_yoy <= -20:
        signals.append({
            "keyword": "营收下降",
            "description": f"营收同比下降{abs(revenue_yoy)}%",
        })

    net_profit_yoy = _as_float(metrics.get("net_profit_yoy"))
    if net_profit_yoy is not None and net_profit_yoy <= -30:
        signals.append({
            "keyword": "净利润下降",
            "description": f"净利润同比下降{abs(net_profit_yoy)}%",
        })

    net_profit = _as_float(metrics.get("net_profit"))
    if net_profit is not None and net_profit < 0:
        signals.append({
            "keyword": "亏损",
            "description": f"净利润为负，录得亏损{abs(net_profit)}亿元",
        })

    gross_margin = _as_float(metrics.get("gross_margin"))
    if gross_margin is not None and gross_margin < 15:
        signals.append({
            "keyword": "毛利率下降",
            "description": f"毛利率降至{gross_margin}%",
        })

    impairment_loss = _as_float(metrics.get("impairment_loss"))
    if impairment_loss is not None and impairment_loss >= 10:
        signals.append({
            "keyword": "资产减值",
            "description": f"计提资产减值{impairment_loss}亿元",
        })

    operating_cash_flow = _as_float(metrics.get("operating_cash_flow"))
    if operating_cash_flow is not None and operating_cash_flow < 0:
        signals.append({
            "keyword": "现金流压力",
            "description": f"经营性现金流为负{abs(operating_cash_flow)}亿元",
        })

    cash_short_debt_ratio = _as_float(metrics.get("cash_short_debt_ratio"))
    if cash_short_debt_ratio is not None and cash_short_debt_ratio < 1:
        signals.append({
            "keyword": "流动性压力",
            "description": f"现金短债比低于1，为{cash_short_debt_ratio}",
        })

    contracted_sales_yoy = _as_float(metrics.get("contracted_sales_yoy"))
    if contracted_sales_yoy is not None and contracted_sales_yoy <= -25:
        signals.append({
            "keyword": "销售下滑",
            "description": f"销售额同比下降{abs(contracted_sales_yoy)}%",
        })

    if not signals:
        signals.append({
            "keyword": "年报",
            "description": "年报未触发重大异常指标，建议进入常规跟踪池",
        })

    return signals


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
