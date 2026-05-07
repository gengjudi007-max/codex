import unittest

from codex.services.policy_semantics import analyze_policy_semantics


class PolicySemanticsTests(unittest.TestCase):
    def test_detect_policy_shift(self):
        previous = "会议提出着力稳定房地产市场，促进房地产市场平稳健康发展。"
        current = "会议提出努力稳定房地产市场，推动房地产市场止跌回稳。"

        result = analyze_policy_semantics(current, previous)

        self.assertTrue(result["semantic_shifts"])
        self.assertEqual(result["news_value"]["level"], "high")
        self.assertIn("稳市场", result["policy_focus"]["categories"])

    def test_detect_land_supply_signal(self):
        result = analyze_policy_semantics(
            "政策提出合理控制新增房地产用地供应，优化土地储备结构。"
        )

        self.assertIn("土地供应", result["policy_focus"]["categories"])
        self.assertTrue(result["reporting_questions"])

    def test_no_policy_signal(self):
        result = analyze_policy_semantics("今天市场成交保持平稳。")

        self.assertEqual(result["news_value"]["level"], "low")
        self.assertFalse(result["current_terms"])


if __name__ == "__main__":
    unittest.main()
