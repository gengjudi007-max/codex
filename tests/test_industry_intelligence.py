import unittest

from codex.services.industry_intelligence import analyze_industry_intelligence


class IndustryIntelligenceTests(unittest.TestCase):
    def test_city_government_support_signal(self):
        payload = {
            "text": "武汉土地市场继续承压，城投拿地和专项债收储仍在持续。",
        }

        result = analyze_industry_intelligence(payload)

        self.assertEqual(
            result["city_cycle"]["dominant_signal"],
            "government_support",
        )

    def test_developer_defensive_signal(self):
        payload = {
            "text": "保利发展继续降负债，并谨慎拿地，强调经营现金流安全。",
        }

        result = analyze_industry_intelligence(payload)

        self.assertEqual(
            result["developer_strategy"]["dominant_signal"],
            "defensive",
        )

    def test_property_service_cycle(self):
        payload = {
            "text": "物业公司开始退出低效项目，应收账款压力持续增加。",
        }

        result = analyze_industry_intelligence(payload)

        self.assertEqual(
            result["property_service_cycle"]["dominant_signal"],
            "quality_contraction",
        )


if __name__ == "__main__":
    unittest.main()
