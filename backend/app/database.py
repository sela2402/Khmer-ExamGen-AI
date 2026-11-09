import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Generator
from uuid import uuid4

from app.config import settings


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    path = Path(settings.database_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            yield connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                owner_user_id TEXT
            );
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                lesson_id TEXT NOT NULL REFERENCES lessons(id),
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                owner_user_id TEXT
            );
            """
        )
        for table in ("lessons", "exams"):
            columns = {
                row["name"]
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
            if "owner_user_id" not in columns:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN owner_user_id TEXT")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS lessons_owner_created "
            "ON lessons(owner_user_id, created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS exams_owner_updated "
            "ON exams(owner_user_id, updated_at DESC)"
        )


def create_lesson(
    filename: str, extracted_text: str, owner_user_id: str
) -> dict[str, Any]:
    lesson_id = str(uuid4())
    with _connect() as connection:
        connection.execute(
            "INSERT INTO lessons (id, filename, extracted_text, owner_user_id) "
            "VALUES (?, ?, ?, ?)",
            (lesson_id, filename, extracted_text, owner_user_id),
        )
    lesson = get_lesson(lesson_id, owner_user_id)
    if lesson is None:
        raise RuntimeError(f"Created lesson {lesson_id} could not be retrieved.")
    return lesson


def get_lesson(lesson_id: str, owner_user_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, filename, extracted_text, created_at FROM lessons "
            "WHERE id = ? AND owner_user_id = ?",
            (lesson_id, owner_user_id),
        ).fetchone()
    return dict(row) if row else None


def list_lessons(owner_user_id: str) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, filename, length(extracted_text) AS character_count, created_at "
            "FROM lessons WHERE owner_user_id = ? ORDER BY created_at DESC",
            (owner_user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_lesson(lesson_id: str, owner_user_id: str) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM lessons WHERE id = ? AND owner_user_id = ?",
            (lesson_id, owner_user_id),
        )
    return cursor.rowcount > 0


def create_exam(
    lesson_id: str, data: dict[str, Any], owner_user_id: str
) -> dict[str, Any]:
    exam_id = str(uuid4())
    with _connect() as connection:
        lesson = connection.execute(
            "SELECT 1 FROM lessons WHERE id = ? AND owner_user_id = ?",
            (lesson_id, owner_user_id),
        ).fetchone()
        if not lesson:
            raise ValueError("Lesson not found for this user.")
        connection.execute(
            "INSERT INTO exams (id, lesson_id, data, owner_user_id) "
            "VALUES (?, ?, ?, ?)",
            (exam_id, lesson_id, json.dumps(data, ensure_ascii=False), owner_user_id),
        )
    exam = get_exam(exam_id, owner_user_id)
    if exam is None:
        raise RuntimeError(f"Created exam {exam_id} could not be retrieved.")
    return exam


def get_exam(exam_id: str, owner_user_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, lesson_id, data, created_at, updated_at FROM exams "
            "WHERE id = ? AND owner_user_id = ?",
            (exam_id, owner_user_id),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "lesson_id": row["lesson_id"],
        **json.loads(row["data"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_exam(
    exam_id: str, data: dict[str, Any], owner_user_id: str
) -> dict[str, Any] | None:
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE exams SET data = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND owner_user_id = ?",
            (json.dumps(data, ensure_ascii=False), exam_id, owner_user_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_exam(exam_id, owner_user_id)


def delete_exam(exam_id: str, owner_user_id: str) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM exams WHERE id = ? AND owner_user_id = ?",
            (exam_id, owner_user_id),
        )
    return cursor.rowcount > 0


def list_exams(owner_user_id: str) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, lesson_id, data, created_at, updated_at FROM exams "
            "WHERE owner_user_id = ? ORDER BY updated_at DESC",
            (owner_user_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "lesson_id": row["lesson_id"],
            **json.loads(row["data"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
