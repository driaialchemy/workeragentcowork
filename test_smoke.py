import importlib
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from store import sqlite_store as store
from utils.ai_client import get_model


class WorkerAgentCoworkSmokeTests(unittest.TestCase):
    def test_core_modules_import(self):
        for module_name in (
            "orchestrator",
            "planner",
            "emailer",
            "workers.web_collector",
            "workers.summarizer",
            "workers.verifier",
            "workers.writer",
        ):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_sqlite_store_round_trip_uses_configured_path(self):
        original_db_path = store.DB_PATH
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "briefing.db"
            store.DB_PATH = str(db_path)
            try:
                store.initialize_db()
                run_id = store.create_run("Claude cost smoke topic")
                article_id = store.save_article(run_id, "https://example.com", "Example", "Content")
                store.save_summary(article_id, run_id, "Summary")
                store.save_verification(run_id, "Claim", "Supported", "Evidence")
                store.save_report(run_id, "Report")
                store.update_run_status(run_id, "complete")

                conn = sqlite3.connect(db_path)
                try:
                    status = conn.execute("SELECT status FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
                    report_count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
                finally:
                    conn.close()

                self.assertEqual(status, "complete")
                self.assertEqual(report_count, 1)
            finally:
                store.DB_PATH = original_db_path

    def test_model_has_default(self):
        self.assertTrue(get_model())


if __name__ == "__main__":
    unittest.main()
