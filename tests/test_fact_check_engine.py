import unittest

from codex.services.fact_check_engine import run_fact_check


class FactCheckEngineTests(unittest.TestCase):
    def test_claim_extraction_and_verification(self):
        text = (
            "保利发展2025年净利润下降40%。"
            "公司称经营现金流已经全面改善。"
            "这表明房地产市场已经彻底复苏。"
        )

        sources = [
            {
                "title": "保利发展2025年年报",
                "source_type": "annual_report",
                "content": "2025年净利润同比下降40%。",
            }
        ]

        result = run_fact_check(text, sources=sources)

        self.assertTrue(result["claims"])
        self.assertTrue(result["evidence_ledger"])
        self.assertEqual(result["verification"]["overall_status"], "needs_verification")

    def test_unsupported_claim(self):
        text = "武汉楼市已经全面领先全国，并必然持续上涨。"

        result = run_fact_check(text)

        self.assertEqual(result["verification"]["overall_status"], "needs_verification")
        self.assertTrue(result["verification"]["results"])

    def test_primary_source_support(self):
        text = "2025年销售额同比下降12%。"

        sources = [
            {
                "title": "企业公告",
                "source_type": "exchange_filing",
                "content": "2025年销售额同比下降12%。",
            }
        ]

        result = run_fact_check(text, sources=sources)

        statuses = [item["status"] for item in result["verification"]["results"]]

        self.assertIn("supported_by_primary_source", statuses)


if __name__ == "__main__":
    unittest.main()
