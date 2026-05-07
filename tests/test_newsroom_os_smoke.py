import tempfile
import unittest
from pathlib import Path

from codex.services.collaboration_os import (
    add_editorial_review,
    add_verification_task,
    create_assignment,
    get_assignment,
    init_collaboration_os,
    update_assignment_status,
)
from codex.services.connector_scheduler import ConnectorScheduler
from codex.services.control_center import build_control_center
from codex.services.executive_intelligence import run_executive_intelligence
from codex.services.health_check import run_health_check
from codex.services.publishing_os import (
    add_approval,
    create_article,
    get_article,
    init_publishing_os,
    publication_gate,
)
from codex.services.queue_runtime import LocalPriorityQueue, build_event
from codex.services.sqlite_store import init_db
from codex.services.worker_runtime import WorkerRuntime


class NewsroomOSSmokeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "newsroom.db")
        init_db(self.db_path)
        init_collaboration_os(self.db_path)
        init_publishing_os(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_check_runs(self):
        result = run_health_check()
        self.assertIn("overall_status", result)

    def test_queue_runtime(self):
        runtime = LocalPriorityQueue()
        runtime.publish(build_event("heartbeat", {"ok": True}))
        self.assertEqual(runtime.size(), 1)
        event = runtime.consume()
        self.assertEqual(event.event_type, "heartbeat")

    def test_scheduler_runtime(self):
        scheduler = ConnectorScheduler()
        scheduler.register_connector("hkex", cadence_seconds=60)
        result = scheduler.run_once()
        self.assertIn("scheduled_connectors", result)
        self.assertEqual(result["queue_size"], 1)

    def test_worker_runtime(self):
        queue_runtime = LocalPriorityQueue()
        queue_runtime.publish(build_event("connector.poll", {"source": "hkex"}))
        worker_runtime = WorkerRuntime(queue_runtime)
        result = worker_runtime.run_once()
        self.assertEqual(result["processed_count"], 1)

    def test_collaboration_workflow(self):
        assignment = create_assignment(
            topic="土地财政风险跟踪",
            db_path=self.db_path,
        )
        assignment_id = assignment["assignment"]["id"]

        update_assignment_status(assignment_id, "reporting", db_path=self.db_path)
        add_verification_task(
            assignment_id,
            claim="城投拿地比例持续上升",
            source_needed="土地成交公告",
            db_path=self.db_path,
        )
        add_editorial_review(
            assignment_id,
            stage="draft_review",
            status="approved",
            reviewer_role="编辑",
            notes="进入下一阶段",
            db_path=self.db_path,
        )

        final_state = get_assignment(assignment_id, db_path=self.db_path)
        self.assertIn("assignment", final_state)
        self.assertIn("verification_tasks", final_state)

    def test_publishing_gate(self):
        article = create_article(
            title="房地产库存与土地财政",
            body="测试稿件",
            db_path=self.db_path,
        )
        article_id = article["article"]["id"]

        add_approval(article_id, "editorial", "approved", "编辑", db_path=self.db_path)
        add_approval(article_id, "fact_check", "approved", "核查", db_path=self.db_path)
        add_approval(article_id, "final", "approved", "主编", db_path=self.db_path)

        gate = publication_gate(article_id, db_path=self.db_path)
        self.assertTrue(gate["can_publish"])

        final_article = get_article(article_id, db_path=self.db_path)
        self.assertIn("article", final_article)

    def test_control_center_runs(self):
        result = build_control_center(db_path=self.db_path)
        self.assertIn("status", result)

    def test_executive_intelligence_runs(self):
        result = run_executive_intelligence(db_path=self.db_path)
        self.assertIn("scenario_planning", result)


if __name__ == "__main__":
    unittest.main()
