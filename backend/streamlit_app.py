import os
from typing import Any

import httpx
import streamlit as st

from app.config import settings

API_BASE_URL = os.getenv("EXAMGEN_API_URL", "http://127.0.0.1:8000").rstrip("/")
QUESTION_TYPES = [
    "Multiple Choice",
    "True or False",
    "Fill in the Blanks",
    "Short Answer",
    "Essay",
    "Problem Solving",
]

NAVIGATION_PAGES: dict[str, Any] = {}


class ApiError(RuntimeError):
    pass


def supabase_auth_request(path: str, payload: dict[str, str]) -> dict[str, Any]:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise ApiError(
            "Supabase sign-in is not configured. Set SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY in backend/.env."
        )
    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/{path}",
            headers={"apikey": settings.supabase_publishable_key},
            json=payload,
            timeout=httpx.Timeout(15, connect=5),
        )
    except httpx.RequestError as error:
        raise ApiError("Could not reach Supabase Auth.") from error
    if not response.is_success:
        try:
            detail = response.json().get("msg") or response.json().get("message")
        except ValueError:
            detail = None
        raise ApiError(detail or f"Supabase sign-in failed ({response.status_code}).")
    return response.json()


def refresh_access_token() -> bool:
    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        return False
    try:
        tokens = supabase_auth_request(
            "token?grant_type=refresh_token", {"refresh_token": refresh_token}
        )
    except ApiError:
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        return False
    st.session_state["access_token"] = tokens["access_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    return True


def api_request(
    method: str,
    path: str,
    *,
    timeout: float = 180,
    **kwargs: Any,
) -> Any:
    try:
        headers = dict(kwargs.pop("headers", {}))
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = httpx.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=httpx.Timeout(timeout, connect=5),
            headers=headers,
            **kwargs,
        )
    except httpx.RequestError as error:
        raise ApiError(
            f"Cannot reach the ExamGen API at {API_BASE_URL}. "
            "Start it with `uvicorn app.main:app --reload` from the backend folder."
        ) from error

    if response.status_code == 401 and refresh_access_token():
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
        try:
            response = httpx.request(
                method,
                f"{API_BASE_URL}{path}",
                timeout=httpx.Timeout(timeout, connect=5),
                headers=headers,
                **kwargs,
            )
        except httpx.RequestError as error:
            raise ApiError(f"Cannot reach the ExamGen API at {API_BASE_URL}.") from error

    if not response.is_success:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        if isinstance(detail, list):
            detail = "; ".join(
                f"{'.'.join(map(str, item.get('loc', [])))}: {item.get('msg', 'Invalid value')}"
                for item in detail
            )
        raise ApiError(str(detail) or f"API request failed ({response.status_code}).")

    if response.status_code == 204:
        return None
    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    return response.content


def lessons() -> list[dict[str, Any]]:
    return api_request("GET", "/api/lessons")


def exams() -> list[dict[str, Any]]:
    return api_request("GET", "/api/exams")


def show_error(error: Exception) -> None:
    st.error(str(error))


def render_sign_in() -> None:
    st.title("Sign in to Khmer ExamGen AI")
    st.write("Use your Supabase Auth account to access lessons and examinations.")
    with st.form("supabase_sign_in"):
        email = st.text_input("Email", autocomplete="email")
        password = st.text_input(
            "Password", type="password", autocomplete="current-password"
        )
        submitted = st.form_submit_button("Sign in", type="primary")
    if not submitted:
        return
    try:
        tokens = supabase_auth_request(
            "token?grant_type=password", {"email": email, "password": password}
        )
        st.session_state["access_token"] = tokens["access_token"]
        st.session_state["refresh_token"] = tokens["refresh_token"]
        st.rerun()
    except ApiError as error:
        show_error(error)


def set_flash(message: str) -> None:
    st.session_state["flash_message"] = message
    st.rerun()


def lesson_selector(
    available_lessons: list[dict[str, Any]], *, key: str
) -> str | None:
    if not available_lessons:
        st.info("Upload a lesson before generating an exam.")
        return None
    lesson_by_id = {lesson["id"]: lesson for lesson in available_lessons}
    lesson_id = st.selectbox(
        "Lesson material",
        options=list(lesson_by_id),
        format_func=lambda item: lesson_by_id[item]["filename"],
        key=key,
    )
    return lesson_id


def render_dashboard() -> None:
    try:
        available_lessons = lessons()
        saved_exams = exams()
    except ApiError as error:
        show_error(error)
        return

    st.title("Khmer ExamGen AI")
    st.write("Create and manage teacher-reviewed examinations from your lesson materials.")
    metric_lesson, metric_exam = st.columns(2)
    metric_lesson.metric("Lesson materials", len(available_lessons))
    metric_exam.metric("Saved examinations", len(saved_exams))

    st.subheader("Recent examinations")
    if not saved_exams:
        st.info("No examinations yet. Use **Generate exam** to create one.")
        return

    for exam in saved_exams[:5]:
        with st.container(border=True):
            title_col, details_col = st.columns([3, 2])
            title_col.markdown(f"**{exam['title']}**")
            title_col.caption(f"Grade {exam['grade']} · {exam['subject']}")
            details_col.caption(
                f"{len(exam['questions'])} questions · "
                f"{exam['total_marks']} marks · {exam['duration_minutes']} min"
            )


def render_lessons() -> None:
    st.title("Lesson library")
    st.write("Upload PDF, DOCX, PPTX, or TXT materials (up to 20 MB).")
    upload_key = f"lesson_upload_{st.session_state.get('upload_revision', 0)}"
    uploaded_file = st.file_uploader(
        "Choose a lesson file",
        type=["pdf", "docx", "pptx", "txt"],
        key=upload_key,
    )
    if st.button(
        "Upload lesson", type="primary", disabled=uploaded_file is None
    ):
        if uploaded_file is None:
            st.error("Choose a lesson file before uploading.")
            return
        try:
            api_request(
                "POST",
                "/api/lessons",
                files={
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream",
                    )
                },
            )
            st.session_state["upload_revision"] = (
                st.session_state.get("upload_revision", 0) + 1
            )
            set_flash(f"Uploaded {uploaded_file.name}.")
        except ApiError as error:
            show_error(error)

    try:
        available_lessons = lessons()
    except ApiError as error:
        show_error(error)
        return

    st.subheader(f"Uploaded lessons ({len(available_lessons)})")
    if not available_lessons:
        st.info("No lesson materials yet.")
        return

    for lesson in available_lessons:
        with st.container(border=True):
            name_col, size_col, action_col = st.columns([3, 2, 1])
            name_col.markdown(f"**{lesson['filename']}**")
            size_col.caption(
                f"{lesson.get('character_count', 0):,} characters · "
                f"{lesson['created_at']}"
            )
            confirm_key = f"confirm_lesson_{lesson['id']}"
            confirmed = action_col.checkbox("Confirm delete", key=confirm_key)
            if action_col.button(
                "Delete",
                key=f"delete_lesson_{lesson['id']}",
                disabled=not confirmed,
            ):
                try:
                    api_request("DELETE", f"/api/lessons/{lesson['id']}")
                    set_flash(f"Deleted {lesson['filename']}. Existing exams are kept.")
                except ApiError as error:
                    show_error(error)


def render_generate() -> None:
    st.title("Generate examination")
    try:
        available_lessons = lessons()
    except ApiError as error:
        show_error(error)
        return

    with st.form("generate_exam"):
        lesson_id = lesson_selector(available_lessons, key="generate_lesson")
        title = st.text_input("Examination title", value="Mid-term Examination")
        grade = st.number_input("Grade", min_value=5, max_value=12, value=9)
        subject = st.text_input("Subject", value="Mathematics")
        total_marks = st.number_input(
            "Total marks", min_value=1, max_value=1000, value=50
        )
        duration_minutes = st.number_input(
            "Duration (minutes)", min_value=1, max_value=600, value=90
        )
        question_count = st.number_input(
            "Number of questions", min_value=1, max_value=100, value=10
        )
        difficulty = st.selectbox(
            "Difficulty", options=["Mixed", "Easy", "Medium", "Hard"]
        )
        question_types = st.multiselect(
            "Question types",
            options=QUESTION_TYPES,
            default=["Multiple Choice", "Short Answer", "Problem Solving"],
        )
        language = st.selectbox("Output language", options=["Khmer", "English"])
        submitted = st.form_submit_button(
            "Generate examination",
            type="primary",
            disabled=not available_lessons,
        )

    if not submitted:
        return
    if not subject.strip():
        st.error("Enter a subject.")
        return
    if total_marks < question_count:
        st.error("Total marks must be at least the number of questions.")
        return
    if not question_types:
        st.error("Select at least one question type.")
        return
    try:
        exam = api_request(
            "POST",
            "/api/exams/generate",
            json={
                "lesson_id": lesson_id,
                "title": title,
                "grade": grade,
                "subject": subject,
                "total_marks": total_marks,
                "duration_minutes": duration_minutes,
                "question_count": question_count,
                "difficulty": difficulty,
                "question_types": question_types,
                "language": language,
            },
        )
        st.session_state["selected_exam_id"] = exam["id"]
        st.session_state["flash_message"] = (
            f"Generated {exam['title']}. Review it before sharing."
        )
        st.switch_page(NAVIGATION_PAGES["examinations"])
    except ApiError as error:
        show_error(error)


def render_examinations() -> None:
    st.title("Examinations")
    try:
        saved_exams = exams()
    except ApiError as error:
        show_error(error)
        return

    if not saved_exams:
        st.info("No saved examinations yet.")
        return

    exam_by_id = {exam["id"]: exam for exam in saved_exams}
    exam_ids = list(exam_by_id)
    current_id = st.session_state.get("selected_exam_id")
    index = exam_ids.index(current_id) if current_id in exam_by_id else 0
    exam_id = st.selectbox(
        "Select examination",
        options=exam_ids,
        index=index,
        format_func=lambda item: exam_by_id[item]["title"],
    )
    try:
        exam = api_request("GET", f"/api/exams/{exam_id}")
    except ApiError as error:
        show_error(error)
        return
    st.session_state["selected_exam_id"] = exam_id
    st.subheader(exam["title"])
    st.caption(
        f"Grade {exam['grade']} · {exam['subject']} · "
        f"{exam['total_marks']} marks · {exam['duration_minutes']} minutes"
    )

    paper_tab, key_tab = st.tabs(["Student paper", "Answer key"])
    for tab, document_type in [(paper_tab, "paper"), (key_tab, "answer_key")]:
        with tab:
            for index, question in enumerate(exam["questions"], start=1):
                with st.expander(
                    f"{index}. {question['text']} ({question['marks']} marks)"
                ):
                    st.caption(f"{question['type']} · {question['difficulty']}")
                    for option_index, option in enumerate(question.get("options", [])):
                        st.write(f"{chr(65 + option_index)}. {option}")
                    if document_type == "answer_key":
                        st.markdown(f"**Answer:** {question['answer']}")
                        if question.get("explanation"):
                            st.write(f"**Explanation:** {question['explanation']}")
                        if question.get("rubric"):
                            st.write(f"**Grading criteria:** {question['rubric']}")

            for format_name in ("docx", "pdf"):
                export_key = f"export_{exam_id}_{document_type}_{format_name}"
                if st.button(
                    f"Prepare {format_name.upper()} download",
                    key=f"prepare_{export_key}",
                ):
                    try:
                        st.session_state[export_key] = api_request(
                            "GET",
                            f"/api/exams/{exam_id}/export",
                            params={
                                "format": format_name,
                                "document": document_type,
                            },
                        )
                    except ApiError as error:
                        show_error(error)
                if export_key in st.session_state:
                    st.download_button(
                        f"Download {format_name.upper()}",
                        data=st.session_state[export_key],
                        file_name=f"{exam['title']}-{document_type}.{format_name}",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                            if format_name == "docx"
                            else "application/pdf"
                        ),
                        key=f"download_{export_key}",
                    )

            if document_type == "answer_key" and st.button(
                "Regenerate answer key", key=f"regenerate_key_{exam_id}"
            ):
                try:
                    api_request("POST", f"/api/exams/{exam_id}/answer-key/regenerate")
                    for format_name in ("docx", "pdf"):
                        st.session_state.pop(
                            f"export_{exam_id}_answer_key_{format_name}", None
                        )
                    set_flash("Regenerated the answer key.")
                except ApiError as error:
                    show_error(error)

            if document_type == "paper":
                for index, question in enumerate(exam["questions"]):
                    if st.button(
                        f"Regenerate question {index + 1}",
                        key=f"regenerate_question_{exam_id}_{index}",
                    ):
                        try:
                            replacement = api_request(
                                "POST",
                                f"/api/exams/{exam_id}/questions/regenerate",
                                json={
                                    "lesson_id": exam["lesson_id"],
                                    "grade": exam["grade"],
                                    "subject": exam["subject"],
                                    "question_type": question["type"],
                                    "difficulty": question["difficulty"],
                                    "language": exam["language"],
                                    "marks": question["marks"],
                                    "existing_questions": [
                                        item["text"]
                                        for question_index, item in enumerate(
                                            exam["questions"]
                                        )
                                        if question_index != index
                                    ],
                                },
                            )
                            exam["questions"][index] = replacement
                            api_request(
                                "PUT",
                                f"/api/exams/{exam_id}",
                                json={
                                    key: exam[key]
                                    for key in (
                                        "title",
                                        "grade",
                                        "subject",
                                        "total_marks",
                                        "duration_minutes",
                                        "language",
                                        "questions",
                                    )
                                },
                            )
                            for format_name in ("docx", "pdf"):
                                st.session_state.pop(
                                    f"export_{exam_id}_paper_{format_name}", None
                                )
                            set_flash(
                                f"Regenerated question {index + 1} and saved the exam."
                            )
                        except ApiError as error:
                            show_error(error)

    st.subheader("Edit examination")
    editor_revision = hash(
        tuple(
            (question["text"], question["answer"], question["marks"])
            for question in exam["questions"]
        )
    )
    with st.form(f"edit_exam_{exam_id}_{editor_revision}"):
        title = st.text_input("Examination title", value=exam["title"])
        subject = st.text_input("Subject", value=exam["subject"])
        questions = []
        for index, question in enumerate(exam["questions"]):
            st.markdown(f"**Question {index + 1}**")
            question_text = st.text_area(
                "Question",
                value=question["text"],
                key=f"edit_{exam_id}_{editor_revision}_{index}_text",
            )
            marks = st.number_input(
                "Marks",
                min_value=1,
                value=question["marks"],
                key=f"edit_{exam_id}_{editor_revision}_{index}_marks",
            )
            difficulty = st.selectbox(
                "Difficulty",
                options=["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(question["difficulty"]),
                key=f"edit_{exam_id}_{editor_revision}_{index}_difficulty",
            )
            answer = st.text_area(
                "Answer",
                value=question["answer"],
                key=f"edit_{exam_id}_{editor_revision}_{index}_answer",
            )
            explanation = st.text_area(
                "Explanation",
                value=question.get("explanation", ""),
                key=f"edit_{exam_id}_{editor_revision}_{index}_explanation",
            )
            rubric = st.text_area(
                "Grading criteria",
                value=question.get("rubric", ""),
                key=f"edit_{exam_id}_{editor_revision}_{index}_rubric",
            )
            updated_question = {
                **question,
                "text": question_text,
                "marks": marks,
                "difficulty": difficulty,
                "answer": answer,
                "explanation": explanation,
                "rubric": rubric,
            }
            if question["type"] == "Multiple Choice":
                options = st.text_area(
                    "Answer choices (one per line)",
                    value="\n".join(question.get("options", [])),
                    key=f"edit_{exam_id}_{editor_revision}_{index}_options",
                )
                updated_question["options"] = options.splitlines()
            questions.append(updated_question)
        save_changes = st.form_submit_button("Save changes", type="primary")

    if save_changes:
        if sum(int(question["marks"]) for question in questions) != int(
            exam["total_marks"]
        ):
            st.error(
                f"Question marks must add up to {exam['total_marks']} before saving."
            )
            return
        try:
            api_request(
                "PUT",
                f"/api/exams/{exam_id}",
                json={
                    "title": title,
                    "grade": exam["grade"],
                    "subject": subject,
                    "total_marks": exam["total_marks"],
                    "duration_minutes": exam["duration_minutes"],
                    "language": exam["language"],
                    "questions": questions,
                },
            )
            for document_type in ("paper", "answer_key"):
                for format_name in ("docx", "pdf"):
                    st.session_state.pop(
                        f"export_{exam_id}_{document_type}_{format_name}", None
                    )
            set_flash("Saved examination changes.")
        except ApiError as error:
            show_error(error)

    st.divider()
    confirmed = st.checkbox(
        "I understand this permanently deletes the examination.",
        key=f"confirm_exam_{exam_id}",
    )
    if st.button("Delete examination", disabled=not confirmed, key=f"delete_exam_{exam_id}"):
        try:
            api_request("DELETE", f"/api/exams/{exam_id}")
            st.session_state.pop("selected_exam_id", None)
            set_flash("Deleted the examination.")
        except ApiError as error:
            show_error(error)


def render_chat() -> None:
    st.title("Chat with AI")
    try:
        available_lessons = lessons()
    except ApiError as error:
        show_error(error)
        return

    lesson_options: dict[str, str | None] = {"No lesson context": None}
    lesson_options.update(
        {lesson["filename"]: lesson["id"] for lesson in available_lessons}
    )
    selected_lesson = st.selectbox("Lesson context", options=list(lesson_options))
    language = st.selectbox("Response language", options=["Khmer", "English"])
    messages = st.session_state.setdefault("chat_messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about your examination or lesson")
    if not prompt:
        return
    messages.append({"role": "user", "content": prompt})
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = api_request(
                    "POST",
                    "/api/chat",
                    json={
                        "messages": messages[-12:],
                        "lesson_id": lesson_options[selected_lesson],
                        "language": language,
                    },
                )
                st.markdown(result["reply"])
        messages.append({"role": "assistant", "content": result["reply"]})
    except ApiError as error:
        show_error(error)
    st.rerun()


def main() -> None:
    st.set_page_config(page_title="Khmer ExamGen AI", page_icon="📚", layout="wide")
    if not st.session_state.get("access_token"):
        render_sign_in()
        return

    pages = [
        st.Page(
            render_dashboard,
            title="Dashboard",
            icon=":material/home:",
            help="See how many lessons and exams are saved, with a list of recent examinations.",
            default=True,
        ),
        st.Page(
            render_lessons,
            title="Lessons",
            icon=":material/folder:",
            help="Upload or delete lesson files used to generate examinations.",
        ),
        st.Page(
            render_generate,
            title="Generate exam",
            icon=":material/add_circle:",
            help="Choose a lesson and settings to generate a teacher-reviewed examination.",
        ),
        st.Page(
            render_examinations,
            title="Examinations",
            icon=":material/description:",
            help="Review, edit, regenerate, export, or delete saved examinations.",
        ),
        st.Page(
            render_chat,
            title="Chat",
            icon=":material/chat:",
            help="Ask the AI assistant questions with optional lesson context.",
        ),
    ]
    NAVIGATION_PAGES["examinations"] = pages[3]
    page = st.navigation(pages, position="top")
    st.sidebar.caption(f"Signed in · API: {API_BASE_URL}")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.session_state.pop("chat_messages", None)
        st.rerun()

    flash_message = st.session_state.pop("flash_message", None)
    if flash_message:
        st.success(flash_message)

    page.run()


if __name__ == "__main__":
    main()
