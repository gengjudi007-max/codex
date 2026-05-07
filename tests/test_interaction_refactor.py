import unittest

from codex.interaction import analyze_payload


class InteractionRefactorCompatibilityTests(unittest.TestCase):
    def test_topic_pipeline_still_available(self):
        result = analyze_payload({"message": "武汉土地市场继续承压"})

        self.assertEqual(result["mode"], "topic_pipeline")
        self.assertIn("topics", result["result"])

    def test_policy_semantics_mode(self):
        result = analyze_payload(
            {
                "policy_semantics": True,
                "current": "会议提出努力稳定房地产市场，推动止跌回稳。",
                "previous": "会议提出着力稳定房地产市场。",
            }
        )

        self.assertEqual(result["mode"], "policy_semantics")
        self.assertIn("semantic_shifts", result["result"])

    def test_risk_chain_mode(self):
        result = analyze_payload(
            {
                "risk_chain": True,
                "summary": "城投拿地增加，土地市场继续依赖地方平台托底。",
            }
        )

        self.assertEqual(result["mode"], "risk_chain")
        self.assertTrue(result["result"]["chains"])

    def test_propaganda_mode(self):
        result = analyze_payload(
            {
                "propaganda_check": True,
                "text": "公司始终坚持高质量发展，持续赋能城市美好生活。",
            }
        )

        self.assertEqual(result["mode"], "propaganda_detect")
        self.assertEqual(result["result"]["risk_level"], "high")


if __name__ == "__main__":
    unittest.main()
