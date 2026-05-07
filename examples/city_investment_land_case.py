from codex.interaction import analyze_payload


def run_city_investment_land_case():
    payload = {
        "mode": "city_investment_land",
        "city": "武汉",
        "yearly": [
            {
                "year": 2021,
                "total_land_transaction_amount": 1800,
                "city_investment_land_amount": 210,
                "total_land_gfa": 6200,
                "city_investment_land_gfa": 760,
                "source": "demo",
            },
            {
                "year": 2022,
                "total_land_transaction_amount": 1350,
                "city_investment_land_amount": 680,
                "total_land_gfa": 5100,
                "city_investment_land_gfa": 2800,
                "source": "demo",
            },
            {
                "year": 2023,
                "total_land_transaction_amount": 920,
                "city_investment_amount_share": 66.5,
                "total_land_gfa": 4300,
                "city_investment_gfa_share": 71.2,
                "source": "demo",
            },
            {
                "year": 2024,
                "total_land_transaction_amount": 760,
                "city_investment_land_amount": 540,
                "total_land_gfa": 3600,
                "city_investment_land_gfa": 2480,
                "source": "demo",
            },
        ],
        "disposal": [
            {"disposal_type": "idle_or_unstarted", "gfa": 820, "amount": 155},
            {"disposal_type": "entrusted_construction", "gfa": 640, "amount": 118},
            {"disposal_type": "co_development", "gfa": 300, "amount": 72},
            {"disposal_type": "land_reserve_repurchase", "gfa": 220, "amount": 66},
        ],
        "special_bonds": [
            {
                "year": 2024,
                "special_bond_issued_amount": 120,
                "land_reserve_repurchase_amount": 70,
                "idle_land_repurchase_amount": 35,
                "related_city_investment_land_book_value": 210,
            },
            {
                "year": 2025,
                "special_bond_issued_amount": 95,
                "land_reserve_repurchase_amount": 50,
                "idle_land_repurchase_amount": 20,
                "related_city_investment_land_book_value": 160,
            },
        ],
    }
    return analyze_payload(payload)


if __name__ == "__main__":
    result = run_city_investment_land_case()["result"]
    print("=== 城投公司兜底拿地专题测试 ===")
    print("对象:", result["subject"])
    print("摘要:")
    for line in result["executive_summary"]:
        print("-", line)
    print("风险:", result["risk_assessment"]["label"], result["risk_assessment"]["score"])
    print("风险驱动:")
    for line in result["risk_assessment"]["drivers"]:
        print("-", line)
