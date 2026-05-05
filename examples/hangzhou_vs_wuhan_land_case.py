from codex.services.city_land_comparator import compare_city_land_markets


def run_hangzhou_vs_wuhan_case():
    """杭州 vs 武汉土地市场城市画像对比。

    注：本案例采用公开报道中的阶段性数据构建演示样本。
    正式报道时，应补充各城市全年土地成交明细、企业属性、地块建面、开工状态和专项债项目级信息。
    """

    cities = [
        {
            "city": "杭州",
            "province": "浙江",
            "year": "2026YTD",
            "tier": "hot_second_tier",
            "metrics": {
                # 2026年4月8日杭州3宗住宅用地全部溢价成交，成交金额58.62亿元，平均溢价率30.8%。
                # 其中华润置地摘得滨江区西兴板块地块，本土民企保亿、兴耀+滨江亦有参与。
                "total_land_amount": 58.62,
                "city_investment_land_amount": 0,
                "city_investment_amount_share": 0,
                "total_land_gfa": None,
                "city_investment_land_gfa": 0,
                "city_investment_gfa_share": 0,
                "private_developer_land_amount": 19.09,
                "central_soe_land_amount": 39.5068,
                "unsold_rate": 0,
                "premium_rate": 30.8,
                "failed_auction_rate": 0,
                "started_gfa_share": None,
                "idle_gfa_share": None,
                "special_bond_land_reserve_amount": None,
            },
            "source": "public_reports_demo_sample",
            "note": "样本采用2026年4月8日杭州三宗宅地成交数据，不代表全年口径。",
        },
        {
            "city": "武汉",
            "province": "湖北",
            "year": "2026YTD",
            "tier": "strong_second_tier",
            "metrics": {
                # 2026年3月27日武汉9宗地揽金15.5423亿元，均由本地国企底价竞得。
                # 2026年4月武汉土地集中放量，核心区地块带动边际回暖，但整体仍偏底价成交。
                "total_land_amount": 21.4833,
                "city_investment_land_amount": 15.5423,
                "city_investment_amount_share": 72.35,
                "total_land_gfa": 56.82,
                "city_investment_land_gfa": 46.26,
                "city_investment_gfa_share": 81.42,
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
            "note": "样本采用2026年3月27日及4月部分公开报道片段，不代表全年口径。",
        },
    ]

    return compare_city_land_markets(cities)


if __name__ == "__main__":
    result = run_hangzhou_vs_wuhan_case()

    print("=== Hangzhou vs Wuhan Land Market Case ===")
    for profile in result["city_profiles"]:
        print(f"\n城市: {profile['city']}")
        print("城投依赖度:", profile["dependency_level"], profile["dependency_score"])
        print("市场恢复程度:", profile["market_recovery_level"], profile["market_recovery_score"])
        print("土地消化风险:", profile["disposal_risk_score"])
        print("专项债闭环风险:", profile["bond_loop_risk_score"])
        print("诊断:")
        for item in profile["diagnosis"]:
            print("-", item)

    print("\n城市分组:")
    print(result["dependency_groups"])
    print(result["market_recovery_groups"])

    print("\n选题:")
    for storyline in result["storylines"]:
        print("-", storyline["title"])
