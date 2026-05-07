import unittest

from codex.services.real_estate_reasoning import reason_real_estate


class RealEstateReasoningTests(unittest.TestCase):
    def test_land_finance_reasoning(self):
        payload = {
            "text": "武汉土地市场继续承压，城投拿地和专项债收储仍在持续。",
        }

        result = reason_real_estate(payload)

        chains = [item["name"] for item in result["causal_chains"]]

        self.assertIn("land_finance_feedback", chains)

    def test_developer_balance_sheet_reasoning(self):
        payload = {
            "text": "保利发展净利润下降，并继续降负债和谨慎拿地。",
        }

        result = reason_real_estate(payload)

        chains = [item["name"] for item in result["causal_chains"]]

        self.assertIn("developer_balance_sheet_contraction", chains)

    def test_policy_transmission_reasoning(self):
        payload = {
            "text": "会议提出止跌回稳，地方继续合理控制新增房地产用地供应。",
            "previous_policy": "会议提出着力稳定房地产市场。",
            "current_policy": "会议提出努力稳定房地产市场，推动止跌回稳。",
        }

        result = reason_real_estate(payload)

        self.assertTrue(result["policy_transmission"])


if __name__ == "__main__":
    unittest.main()
