import json
import tempfile
import unittest
from pathlib import Path

from codex.services.continuous_runner import run_once


class ContinuousRunnerTests(unittest.TestCase):
    def test_run_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "watchlist.json"

            config = {
                "texts": [
                    "武汉土地市场继续承压，城投托底仍在持续。"
                ],
                "items": [
                    {
                        "title": "保利发展2025年年报",
                        "source_type": "annual_report",
                        "content": "净利润下降40%。"
                    }
                ],
                "store_path": str(Path(tmpdir) / "sources.jsonl"),
                "memory_path": str(Path(tmpdir) / "memory.jsonl"),
                "run_log_path": str(Path(tmpdir) / "runlog.jsonl")
            }

            config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

            result = run_once(str(config_path))

            self.assertTrue(result["ingestion"]["accepted_count"] > 0)
            self.assertTrue(result["alerts"])


if __name__ == "__main__":
    unittest.main()
