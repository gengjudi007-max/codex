from codex.services.city_land_comparator import compare_city_land_markets


def run_wuhan_case():
    """武汉城投拿地与城市土地市场画像示例。

    注：本案例采用公开报道中的阶段性数据构建演示样本。
    正式报道时，应进一步补充自然资源部门地块明细、成交确认书、专项债募集说明书和地块开工状态。
    """

    cities = [
        {
            "city": "武汉",
            "province": "湖北",
            "year": "2026YTD",
            "tier": "strong_second_tier",
            "metrics": {
                # 2026年1月中指口径：土地出让金3.72亿元，同比下降43.7%。
                # 2026年3月27日土拍：9宗地揽金15.54亿元，经开产投、车谷城发等国企底价包揽。
                # 2026年4月21日土拍：6宗地成交2.2233亿元，竞得方涵盖本地国企及民营企业。
                "total_land_amount": 21.4833,
                "city_investment_land_amount": 15.54,
                "city_investment_amount_share": 72.34,
                "total_land_gfa": 56.82,
                "city_investment_land_gfa": None,
                "city_investment_gfa_share": None,
                "private_developer_land_amount": 2.81,
                "central_soe_land_amount": None,
                "unsold_rate": None,
                "premium_rate": 0,
                "failed_auction_rate": None,
                "started_gfa_share": None,
                "idle_gfa_share": None,
                "special_bond_land_reserve_amount": None,
            },
            "source": "public_reports_demo_sample",
            "note": "示例仅覆盖2026年1月、3月27日、4月21日等公开报道片段，不等同于武汉全年或截至4月底全部成交口径。",
        }
    ]

    return compare_city_land_markets(cities)


if __name__ == "__main__":
    result = run_wuhan_case()
    profile = result["city_profiles"][0]

    print("=== Wuhan City Land Case ===")
    print("城市:", profile["city"])
    print("城投依赖度:", profile["dependency_level"], profile["dependency_score"])
    print("市场恢复程度:", profile["market_recovery_level"], profile["market_recovery_score"])
    print("土地消化风险:", profile["disposal_risk_score"])
    print("专项债闭环风险:", profile["bond_loop_risk_score"])
    print("诊断:")
    for item in profile["diagnosis"]:
        print("-", item)

    print("\n选题:")
    for storyline in result["storylines"]:
        print("-", storyline["title"])
