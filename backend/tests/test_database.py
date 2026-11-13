import sqlite3
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from app import database
from app.config import settings


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.previous_url = settings.database_url
        self.previous_path = settings.database_path
        self.temp_dir = tempfile.TemporaryDirectory()
        settings.database_url = ""
        settings.database_path = str(Path(self.temp_dir.name) / "test.sqlite3")
        database._get_engine.cache_clear()
        self.engine = database._engine()
        database.initialize_database()

    def tearDown(self):
        self.engine.dispose()
        database._get_engine.cache_clear()
        settings.database_url = self.previous_url
        settings.database_path = self.previous_path
        self.temp_dir.cleanup()

    def test_owner_scoped_lesson_and_exam_crud(self):
        lesson = database.create_lesson("lesson.txt", "Khmer lesson", "user-1")
        self.assertEqual(lesson["extracted_text"], "Khmer lesson")
        self.assertIsNone(database.get_lesson(lesson["id"], "user-2"))
        self.assertEqual(
            database.list_lessons("user-1")[0]["character_count"],
            len("Khmer lesson"),
        )

        exam = database.create_exam(
            lesson["id"],
            {"title": "Unit 1", "questions": [{"prompt": "Question"}]},
            "user-1",
        )
        self.assertEqual(exam["title"], "Unit 1")
        self.assertIsNone(database.get_exam(exam["id"], "user-2"))

        updated = database.update_exam(
            exam["id"], {"title": "Updated"}, "user-1"
        )
        self.assertEqual(updated["title"], "Updated")
        self.assertEqual(len(database.list_exams("user-1")), 1)
        self.assertFalse(database.delete_exam(exam["id"], "user-2"))
        self.assertTrue(database.delete_exam(exam["id"], "user-1"))

    def test_initialize_adds_owner_columns_to_existing_tables(self):
        legacy_path = Path(self.temp_dir.name) / "legacy.sqlite3"
        self.engine.dispose()
        database._get_engine.cache_clear()
        settings.database_path = str(legacy_path)
        connection = sqlite3.connect(legacy_path)
        try:
            connection.executescript(
                """
                CREATE TABLE lessons (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    extracted_text TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE exams (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        finally:
            connection.close()

        self.engine = database._engine()
        database.initialize_database()
        inspector = inspect(self.engine)
        for table in ("lessons", "exams"):
            columns = {column["name"] for column in inspector.get_columns(table)}
            self.assertIn("owner_user_id", columns)

    def test_pooler_url_uses_psycopg_without_prisma_query_parameter(self):
        engine = database._get_engine(
            "postgresql://user:password@localhost:5432/db?pgbouncer=true",
            "",
        )
        try:
            self.assertEqual(engine.url.drivername, "postgresql+psycopg")
            self.assertNotIn("pgbouncer", engine.url.query)
            self.assertEqual(engine.url.query["sslmode"], "require")
        finally:
            engine.dispose()
            database._get_engine.cache_clear()
