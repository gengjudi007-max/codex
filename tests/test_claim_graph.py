import unittest

from codex.services.claim_graph import build_claim_graph


class ClaimGraphTests(unittest.TestCase):
    def test_claim_graph_building(self):
        texts = [
            "保利发展2025年净利润下降40%。",
            "保利发展2025年净利润下降25%。",
        ]

        sources = [
            {
                "title": "保利发展2025年年报",
                "source_type": "annual_report",
                "content": "2025年净利润同比下降40%。",
            }
        ]

        graph = build_claim_graph(texts, sources=sources)

        self.assertGreater(graph["node_count"], 0)
        self.assertGreater(graph["edge_count"], 0)
        self.assertTrue(graph["contradictions"]["contradictions"])

    def test_claim_graph_has_verification_actions(self):
        texts = [
            "武汉楼市已经彻底复苏，并必然持续上涨。"
        ]

        graph = build_claim_graph(texts)

        action_nodes = [
            node for node in graph["nodes"]
            if node["type"] == "verification_action"
        ]

        self.assertTrue(action_nodes)

    def test_claim_graph_has_source_support(self):
        texts = [
            "2025年销售额同比下降12%。"
        ]

        sources = [
            {
                "title": "企业公告",
                "source_type": "exchange_filing",
                "content": "2025年销售额同比下降12%。",
            }
        ]

        graph = build_claim_graph(texts, sources=sources)

        support_edges = [
            edge for edge in graph["edges"]
            if edge["relation"] == "supports"
        ]

        self.assertTrue(support_edges)


if __name__ == "__main__":
    unittest.main()
