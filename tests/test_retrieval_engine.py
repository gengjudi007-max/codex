import tempfile
import unittest
from pathlib import Path

from codex.services.retrieval_engine import (
    alerts_query,
    claims_query,
    entity_query,
    newsroom_summary,
    search_newsroom,
    timeline_query,
)
from codex.services.sqlite_store import (
    init_db,
    save_alerts,
    save_claims,
    save_memory_events,
    save_sources,
)


class RetrievalEngineTests(unittest.TestCase):
    def test_retrieval_queries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "newsroom.db")
            init_db(db_path)

            save_sources(
                [
                    {
                        "title": "武汉土地市场",
                        "source_type": "land_transaction",
                        "city": "武汉",
                        "company": "武汉城投",
                        "content": "城投继续托底。",
                    }
                ],
                db_path,
            )

            save_memory_events(
                [
                    {
                        "id": "event-1",
                        "title": "武汉土地托底",
                        "city": "武汉",
                        "company": "武汉城投",
                        "risks": ["土地财政压力"],
                        "risk_chains": ["land_finance_feedback"],
                        "content": "专项债收储。",
                    }
                ],
                db_path,
            )

            save_claims(
                {
                    "verification": {
                        "results": [
                            {
                                "claim": "武汉城投继续托底",
                                "type": "market",
                                "status": "verified",
                                "source_count": 2,
                                "best_source_score": 90,
                            }
                        ]
                    }
                },
                db_path,
            )

            save_alerts(["发现风险链信号"], db_path=db_path)

            self.assertTrue(search_newsroom("武汉", db_path)["sources"]["matched"] > 0)
            self.assertTrue(timeline_query("武汉", db_path)["event_count"] > 0)
            self.assertTrue(entity_query("武汉", db_path)["source_count"] > 0)
            self.assertTrue(claims_query("verified", db_path)["claim_count"] > 0)
            self.assertTrue(alerts_query(db_path)["alert_count"] > 0)
            self.assertTrue(newsroom_summary(db_path)["run_count"] >= 0)


if __name__ == "__main__":
    unittest.main()
