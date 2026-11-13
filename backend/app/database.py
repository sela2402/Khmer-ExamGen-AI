import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Text,
    create_engine,
    delete,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.config import settings


class Base(DeclarativeBase):
    pass


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    owner_user_id: Mapped[str | None] = mapped_column(Text)


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    lesson_id: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    owner_user_id: Mapped[str | None] = mapped_column(Text)


@lru_cache(maxsize=8)
def _get_engine(database_url: str, database_path: str) -> Engine:
    if database_url:
        url = make_url(database_url)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+psycopg")
        query = dict(url.query)
        query.pop("pgbouncer", None)
        query.setdefault("sslmode", "require")
        url = url.set(query=query)
        return create_engine(
            url,
            connect_args={"prepare_threshold": None},
            pool_pre_ping=True,
        )

    path = Path(database_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = URL.create("sqlite", database=str(path))
    return create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
    )


def _engine() -> Engine:
    return _get_engine(settings.database_url, settings.database_path)


def initialize_database() -> None:
    engine = _engine()
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table in ("lessons", "exams"):
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "owner_user_id" not in columns:
                connection.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN owner_user_id TEXT")
                )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS lessons_owner_created "
                "ON lessons(owner_user_id, created_at DESC)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS exams_owner_updated "
                "ON exams(owner_user_id, updated_at DESC)"
            )
        )


def create_lesson(
    filename: str, extracted_text: str, owner_user_id: str
) -> dict[str, Any]:
    lesson_id = str(uuid4())
    with Session(_engine()) as session, session.begin():
        session.add(
            Lesson(
                id=lesson_id,
                filename=filename,
                extracted_text=extracted_text,
                owner_user_id=owner_user_id,
            )
        )
    lesson = get_lesson(lesson_id, owner_user_id)
    if lesson is None:
        raise RuntimeError(f"Created lesson {lesson_id} could not be retrieved.")
    return lesson


def get_lesson(lesson_id: str, owner_user_id: str) -> dict[str, Any] | None:
    with Session(_engine()) as session:
        lesson = session.scalar(
            select(Lesson).where(
                Lesson.id == lesson_id,
                Lesson.owner_user_id == owner_user_id,
            )
        )
        if lesson is None:
            return None
        return {
            "id": lesson.id,
            "filename": lesson.filename,
            "extracted_text": lesson.extracted_text,
            "created_at": lesson.created_at,
        }


def list_lessons(owner_user_id: str) -> list[dict[str, Any]]:
    with Session(_engine()) as session:
        rows = session.execute(
            select(
                Lesson.id,
                Lesson.filename,
                func.length(Lesson.extracted_text).label("character_count"),
                Lesson.created_at,
            )
            .where(Lesson.owner_user_id == owner_user_id)
            .order_by(Lesson.created_at.desc())
        )
        return [dict(row._mapping) for row in rows]


def delete_lesson(lesson_id: str, owner_user_id: str) -> bool:
    with Session(_engine()) as session, session.begin():
        result = session.execute(
            delete(Lesson).where(
                Lesson.id == lesson_id,
                Lesson.owner_user_id == owner_user_id,
            )
        )
        return result.rowcount > 0


def create_exam(
    lesson_id: str, data: dict[str, Any], owner_user_id: str
) -> dict[str, Any]:
    exam_id = str(uuid4())
    with Session(_engine()) as session, session.begin():
        lesson_exists = session.scalar(
            select(Lesson.id).where(
                Lesson.id == lesson_id,
                Lesson.owner_user_id == owner_user_id,
            )
        )
        if lesson_exists is None:
            raise ValueError("Lesson not found for this user.")
        session.add(
            Exam(
                id=exam_id,
                lesson_id=lesson_id,
                data=json.dumps(data, ensure_ascii=False),
                owner_user_id=owner_user_id,
            )
        )
    exam = get_exam(exam_id, owner_user_id)
    if exam is None:
        raise RuntimeError(f"Created exam {exam_id} could not be retrieved.")
    return exam


def get_exam(exam_id: str, owner_user_id: str) -> dict[str, Any] | None:
    with Session(_engine()) as session:
        exam = session.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.owner_user_id == owner_user_id,
            )
        )
        return _exam_to_dict(exam) if exam else None


def update_exam(
    exam_id: str, data: dict[str, Any], owner_user_id: str
) -> dict[str, Any] | None:
    with Session(_engine()) as session, session.begin():
        exam = session.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.owner_user_id == owner_user_id,
            )
        )
        if exam is None:
            return None
        exam.data = json.dumps(data, ensure_ascii=False)
    return get_exam(exam_id, owner_user_id)


def delete_exam(exam_id: str, owner_user_id: str) -> bool:
    with Session(_engine()) as session, session.begin():
        result = session.execute(
            delete(Exam).where(
                Exam.id == exam_id,
                Exam.owner_user_id == owner_user_id,
            )
        )
        return result.rowcount > 0


def list_exams(owner_user_id: str) -> list[dict[str, Any]]:
    with Session(_engine()) as session:
        exams = session.scalars(
            select(Exam)
            .where(Exam.owner_user_id == owner_user_id)
            .order_by(Exam.updated_at.desc())
        ).all()
        return [_exam_to_dict(exam) for exam in exams]


def _exam_to_dict(exam: Exam) -> dict[str, Any]:
    return {
        "id": exam.id,
        "lesson_id": exam.lesson_id,
        **json.loads(exam.data),
        "created_at": exam.created_at,
        "updated_at": exam.updated_at,
    }
