from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.auth import require_authenticated_user
from app.config import settings
from app.database import (
    create_exam,
    create_lesson,
    delete_exam,
    delete_lesson,
    get_exam,
    get_lesson,
    initialize_database,
    list_exams,
    list_lessons,
    update_exam,
)
from app.documents import SUPPORTED_EXTENSIONS, extract_text
from app.exporters import content_disposition, export_exam
from app.generator import (
    GenerationError,
    chat_with_teacher,
    generate_exam,
    regenerate_answer_key,
    regenerate_question,
)
from app.schemas import ChatRequest, ExamData, ExamUpdate, GenerateRequest, RegenerateQuestionRequest

app = FastAPI(title="Khmer ExamGen AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/lessons")
def lessons(user: dict = Depends(require_authenticated_user)) -> list[dict]:
    return list_lessons(user["sub"])


@app.post("/api/lessons", status_code=201)
async def upload_lesson(
    file: UploadFile = File(...),
    user: dict = Depends(require_authenticated_user),
) -> dict:
    filename = file.filename or "lesson"
    if not filename.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
        raise HTTPException(status_code=415, detail="Upload a PDF, DOCX, PPTX, or TXT file.")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.")
    try:
        text = extract_text(filename, content)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    lesson = create_lesson(filename, text, user["sub"])
    return {
        "id": lesson["id"],
        "filename": lesson["filename"],
        "character_count": len(lesson["extracted_text"]),
        "preview": lesson["extracted_text"][:1200],
        "created_at": lesson["created_at"],
    }


@app.delete("/api/lessons/{lesson_id}", status_code=204)
def remove_lesson(
    lesson_id: str, user: dict = Depends(require_authenticated_user)
) -> Response:
    if not delete_lesson(lesson_id, user["sub"]):
        raise HTTPException(status_code=404, detail="Lesson not found.")
    return Response(status_code=204)


@app.get("/api/exams")
def exams(user: dict = Depends(require_authenticated_user)) -> list[dict]:
    return list_exams(user["sub"])


@app.post("/api/chat")
async def teacher_chat(
    request: ChatRequest, user: dict = Depends(require_authenticated_user)
) -> dict[str, str]:
    lesson_text = ""
    if request.lesson_id:
        lesson = get_lesson(request.lesson_id, user["sub"])
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        lesson_text = lesson["extracted_text"]
    try:
        reply = await chat_with_teacher(request, lesson_text)
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"reply": reply}


@app.post("/api/exams/generate", status_code=201)
async def create_generated_exam(
    request: GenerateRequest, user: dict = Depends(require_authenticated_user)
) -> dict:
    lesson = get_lesson(request.lesson_id, user["sub"])
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found. Upload a lesson before generating an exam.")
    try:
        data = await generate_exam(request, lesson["extracted_text"])
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return create_exam(request.lesson_id, data, user["sub"])


@app.get("/api/exams/{exam_id}")
def read_exam(exam_id: str, user: dict = Depends(require_authenticated_user)) -> dict:
    exam = get_exam(exam_id, user["sub"])
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    return exam


@app.put("/api/exams/{exam_id}")
def save_exam(
    exam_id: str,
    update: ExamUpdate,
    user: dict = Depends(require_authenticated_user),
) -> dict:
    data = update.model_dump()
    try:
        ExamData.model_validate(data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    exam = update_exam(exam_id, data, user["sub"])
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    return exam


@app.delete("/api/exams/{exam_id}", status_code=204)
def remove_exam(
    exam_id: str, user: dict = Depends(require_authenticated_user)
) -> Response:
    if not delete_exam(exam_id, user["sub"]):
        raise HTTPException(status_code=404, detail="Exam not found.")
    return Response(status_code=204)


@app.post("/api/exams/{exam_id}/questions/regenerate")
async def regenerate_exam_question(
    exam_id: str,
    request: RegenerateQuestionRequest,
    user: dict = Depends(require_authenticated_user),
) -> dict:
    exam = get_exam(exam_id, user["sub"])
    lesson = get_lesson(request.lesson_id, user["sub"])
    if not exam or not lesson:
        raise HTTPException(status_code=404, detail="Exam or lesson not found.")
    try:
        return await regenerate_question(request, lesson["extracted_text"])
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/exams/{exam_id}/answer-key/regenerate")
async def regenerate_exam_answer_key(
    exam_id: str, user: dict = Depends(require_authenticated_user)
) -> dict:
    exam = get_exam(exam_id, user["sub"])
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    lesson = get_lesson(exam["lesson_id"], user["sub"])
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")
    try:
        answers = await regenerate_answer_key(exam, lesson["extracted_text"])
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    for question, answer in zip(exam["questions"], answers):
        question.update({key: answer.get(key, "") for key in ("answer", "explanation", "rubric")})
    updated = update_exam(exam_id, {key: exam[key] for key in (
        "title", "grade", "subject", "total_marks", "duration_minutes", "language", "questions"
    )}, user["sub"])
    return updated  # type: ignore[return-value]


@app.get("/api/exams/{exam_id}/export")
def download_exam(
    exam_id: str,
    format: str = Query(pattern="^(pdf|docx)$"),
    document: str = Query(pattern="^(paper|answer_key)$"),
    user: dict = Depends(require_authenticated_user),
) -> Response:
    exam = get_exam(exam_id, user["sub"])
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    try:
        content, media_type, filename = export_exam(exam, format, document)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition(filename)},
    )
