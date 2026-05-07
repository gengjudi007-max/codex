import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from codex.services.newsroom_orchestrator import run_newsroom_orchestrator


class NewsroomOrchestratorTests(unittest.TestCase):
    def test_full_newsroom_pipeline(self):
        with TemporaryDirectory() as tmpdir:
            memory_path = str(Path(tmpdir) / "memory.jsonl")

            payload = {
                "memory_path": memory_path,
                "items": [
                    {
                        "title": "武汉土地市场继续承压",
                        "summary": "城投托底持续，专项债支持收储。",
                    },
                    {
                        "title": "保利发展利润下降",
                        "summary": "企业减值增加，经营现金流承压。",
                    },
                ],
                "draft": "公司始终坚持高质量发展，持续赋能城市美好生活。",
                "previous_policy": "会议提出着力稳定房地产市场。",
                "current_policy": "会议提出努力稳定房地产市场，推动止跌回稳。",
            }

            result = run_newsroom_orchestrator(payload)

            self.assertEqual(result["mode"], "newsroom_orchestrator")
            self.assertIn("topics", result)
            self.assertIn("intelligence", result)
            self.assertIn("editorial", result)
            self.assertTrue(result["intelligence"]["risk_chain"]["chains"])
            self.assertTrue(result["intelligence"]["policy_semantics"]["semantic_shifts"])
            self.assertEqual(
                result["editorial"]["propaganda_check"]["risk_level"],
                "high",
            )

    def test_orchestrator_without_draft(self):
        with TemporaryDirectory() as tmpdir:
            memory_path = str(Path(tmpdir) / "memory.jsonl")

            result = run_newsroom_orchestrator(
                {
                    "memory_path": memory_path,
                    "message": "物业公司退出低效项目，应收账款压力增加。",
                }
            )

            self.assertEqual(result["mode"], "newsroom_orchestrator")
            self.assertIsNone(result["editorial"])
            self.assertTrue(result["topics"]["topics"])


if __name__ == "__main__":
    unittest.main()
