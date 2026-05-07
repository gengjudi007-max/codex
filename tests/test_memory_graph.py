import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from codex.services.memory_graph import (
    build_timeline,
    link_related_events,
    memory_summary,
    query_memory,
    remember_events,
)


class MemoryGraphTests(unittest.TestCase):
    def test_remember_and_query(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "武汉土地市场继续承压",
                        "summary": "城投托底仍在持续，土地财政压力加大。",
                        "occurred_at": "2025-03",
                    },
                    {
                        "title": "保利发展利润下降",
                        "summary": "企业减值增加，经营现金流承压。",
                        "occurred_at": "2025-04",
                    },
                ],
                path=path,
            )

            result = query_memory(query="城投托底", path=path)

            self.assertEqual(result["matched"], 1)
            self.assertEqual(result["events"][0]["city"], "武汉")

    def test_build_timeline(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "武汉土地市场继续承压",
                        "summary": "城投托底仍在持续。",
                        "occurred_at": "2024-01",
                    },
                    {
                        "title": "武汉专项债支持收储",
                        "summary": "地方继续推进库存去化。",
                        "occurred_at": "2025-01",
                    },
                ],
                path=path,
            )

            timeline = build_timeline("武汉", path=path)

            self.assertEqual(timeline["event_count"], 2)
            self.assertEqual(timeline["timeline"][0]["occurred_at"], "2024-01")

    def test_related_events(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "武汉土地市场继续承压",
                        "summary": "城投托底仍在持续，土地财政压力加大。",
                    }
                ],
                path=path,
            )

            related = link_related_events(
                {
                    "title": "武汉专项债支持土地收储",
                    "summary": "地方平台继续托底土地市场。",
                },
                path=path,
            )

            self.assertTrue(related["related_events"])

    def test_memory_summary(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "物业公司退出低效项目",
                        "summary": "应收账款压力增加。",
                    }
                ],
                path=path,
            )

            summary = memory_summary(path=path)

            self.assertEqual(summary["event_count"], 1)
            self.assertIn("应收账款", summary["risks"])


if __name__ == "__main__":
    unittest.main()
