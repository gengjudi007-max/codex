import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from codex.services.entity_graph import (
    build_entity_graph,
    entity_profile,
    graph_summary,
)
from codex.services.memory_graph import remember_events


class EntityGraphTests(unittest.TestCase):
    def test_build_entity_graph(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "武汉土地市场承压",
                        "summary": "城投托底持续，土地财政压力加大。",
                        "city": "武汉",
                    },
                    {
                        "title": "保利发展利润下降",
                        "summary": "减值增加，经营现金流承压。",
                        "company": "保利发展",
                    },
                ],
                path=path,
            )

            graph = build_entity_graph(path=path)

            self.assertGreater(graph["node_count"], 0)
            self.assertGreater(graph["edge_count"], 0)

    def test_entity_profile(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "memory.jsonl")

            remember_events(
                [
                    {
                        "title": "武汉专项债支持收储",
                        "summary": "库存去化压力仍需观察。",
                        "city": "武汉",
                    }
                ],
                path=path,
            )

            profile = entity_profile("武汉", path=path)

            self.assertEqual(profile["event_count"], 1)
            self.assertTrue(profile["recent_events"])

    def test_graph_summary(self):
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

            summary = graph_summary(path=path)

            self.assertGreater(summary["node_count"], 0)
            self.assertIn("risk", summary["node_type_counts"])


if __name__ == "__main__":
    unittest.main()
