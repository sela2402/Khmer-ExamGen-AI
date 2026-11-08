import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings


def _connect() -> sqlite3.Connection:
    path = Path(settings.database_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                lesson_id TEXT NOT NULL REFERENCES lessons(id),
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def create_lesson(filename: str, extracted_text: str) -> dict[str, Any]:
    lesson_id = str(uuid4())
    with _connect() as connection:
        connection.execute(
            "INSERT INTO lessons (id, filename, extracted_text) VALUES (?, ?, ?)",
            (lesson_id, filename, extracted_text),
        )
    return get_lesson(lesson_id)


def get_lesson(lesson_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, filename, extracted_text, created_at FROM lessons WHERE id = ?",
            (lesson_id,),
        ).fetchone()
    return dict(row) if row else None


def list_lessons() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, filename, length(extracted_text) AS character_count, created_at "
            "FROM lessons ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def create_exam(lesson_id: str, data: dict[str, Any]) -> dict[str, Any]:
    exam_id = str(uuid4())
    with _connect() as connection:
        connection.execute(
            "INSERT INTO exams (id, lesson_id, data) VALUES (?, ?, ?)",
            (exam_id, lesson_id, json.dumps(data, ensure_ascii=False)),
        )
    return get_exam(exam_id)  # type: ignore[return-value]


def get_exam(exam_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, lesson_id, data, created_at, updated_at FROM exams WHERE id = ?",
            (exam_id,),
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


def update_exam(exam_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE exams SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(data, ensure_ascii=False), exam_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_exam(exam_id)


def list_exams() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, lesson_id, data, created_at, updated_at FROM exams ORDER BY updated_at DESC"
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
