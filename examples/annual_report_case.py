from codex.interaction import analyze_payload


def run_annual_report_case():
    payload = {
        "report": {
            "company": "保利发展",
            "year": "2025",
            "metrics": {
                "revenue_yoy": -22.5,
                "net_profit_yoy": -40,
                "gross_margin": 13.8,
                "impairment_loss": 35,
                "operating_cash_flow": -10,
                "cash_short_debt_ratio": 0.8,
            },
        }
    }
    return analyze_payload(payload)


if __name__ == "__main__":
    result = run_annual_report_case()
    pipeline = result["result"]["topic_pipeline"]
    print(pipeline["message"])
    for topic in pipeline["topics"]:
        print("-", topic["topic"])
