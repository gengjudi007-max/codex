import unittest

from codex.services.risk_chain import analyze_risk_chain


class RiskChainTests(unittest.TestCase):
    def test_city_investment_land_chain(self):
        payload = {
            "title": "武汉多宗土地底价成交",
            "summary": "城投拿地占比提升，地方平台继续托底土地市场。",
        }

        result = analyze_risk_chain(payload)

        self.assertTrue(result["chains"])
        self.assertIn("地方财政压力", result["risk_map"]["nodes"])

    def test_developer_finance_chain(self):
        payload = {
            "summary": "房企净利润下降，资产减值增加，经营现金流转负。"
        }

        result = analyze_risk_chain(payload)

        self.assertTrue(result["chains"])
        self.assertEqual(result["chains"][0]["chain"], "developer_finance")

    def test_empty_signal(self):
        result = analyze_risk_chain("今天天气很好。")

        self.assertFalse(result["chains"])
        self.assertIn("补充政策文件", result["reporting_path"][0])


if __name__ == "__main__":
    unittest.main()
