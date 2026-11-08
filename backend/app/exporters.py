from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.config import settings


def _is_answer_key(document_type: str) -> bool:
    if document_type not in {"paper", "answer_key"}:
        raise ValueError("Document type must be paper or answer_key.")
    return document_type == "answer_key"


def _labels(exam: dict) -> dict[str, str]:
    if exam.get("language") == "Khmer":
        return {
            "grade": "ថ្នាក់ទី",
            "subject": "មុខវិជ្ជា",
            "marks": "ពិន្ទុ",
            "duration": "នាទី",
            "teacher_copy": "គន្លឹះចម្លើយ — ច្បាប់ចម្លងសម្រាប់គ្រូ",
            "student_info": "ឈ្មោះ៖ ______________________________    ថ្នាក់៖ __________    កាលបរិច្ឆេទ៖ __________",
            "instructions": "សេចក្តីណែនាំ៖ សូមឆ្លើយគ្រប់សំណួរ។",
            "answer": "ចម្លើយ",
            "explanation": "ការពន្យល់",
            "rubric": "លក្ខណៈវិនិច្ឆ័យដាក់ពិន្ទុ",
        }
    return {
        "grade": "Grade",
        "subject": "Subject",
        "marks": "marks",
        "duration": "minutes",
        "teacher_copy": "ANSWER KEY — TEACHER COPY",
        "student_info": "Name: ______________________________    Class: __________    Date: __________",
        "instructions": "Instructions: Answer all questions.",
        "answer": "Answer",
        "explanation": "Explanation",
        "rubric": "Grading criteria",
    }


def _docx(exam: dict, document_type: str) -> bytes:
    answer_key = _is_answer_key(document_type)
    labels = _labels(exam)
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    style = document.styles["Normal"]
    style.font.name = "Noto Sans Khmer"
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", "Noto Sans Khmer"
    )
    heading = document.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run(exam["title"]).bold = True
    subtitle = document.add_paragraph(
        f"{labels['grade']} {exam['grade']} | {labels['subject']}: {exam['subject']} | "
        f"{exam['total_marks']} {labels['marks']} | {exam['duration_minutes']} {labels['duration']}"
    )
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if answer_key:
        label = document.add_paragraph(labels["teacher_copy"])
        label.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label.runs[0].bold = True
    else:
        document.add_paragraph(labels["student_info"])
        document.add_paragraph(labels["instructions"])
    for number, question in enumerate(exam["questions"], start=1):
        document.add_paragraph(
            f"{number}. [{question['marks']} {labels['marks']}] "
            f"{question['text'] if not answer_key else question['text']}"
        )
        if answer_key:
            document.add_paragraph(f"{labels['answer']}: {question['answer']}")
            if question.get("explanation"):
                document.add_paragraph(f"{labels['explanation']}: {question['explanation']}")
            if question.get("rubric"):
                document.add_paragraph(f"{labels['rubric']}: {question['rubric']}")
        else:
            for option_number, option in enumerate(question.get("options", [])):
                document.add_paragraph(f"   {chr(65 + option_number)}. {option}")
            if question["type"] in {"Short Answer", "Essay", "Problem Solving"}:
                document.add_paragraph("\n\n")
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _register_khmer_font() -> str:
    candidates = [
        settings.khmer_font_path,
        r"C:\Windows\Fonts\NotoSansKhmer-Regular.ttf",
        r"C:\Windows\Fonts\khmerui.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKhmer-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKhmer-VF.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            pdfmetrics.registerFont(TTFont("ExamGenKhmer", candidate))
            return "ExamGenKhmer"
    return "Helvetica"


def _pdf(exam: dict, document_type: str) -> bytes:
    answer_key = _is_answer_key(document_type)
    labels = _labels(exam)
    font_name = _register_khmer_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ExamTitle", parent=styles["Title"], fontName=font_name, alignment=TA_CENTER, fontSize=16, leading=23
    )
    body_style = ParagraphStyle(
        "ExamBody", parent=styles["BodyText"], fontName=font_name, fontSize=11, leading=18, spaceAfter=8
    )
    story = [
        Paragraph(escape(exam["title"]), title_style),
        Paragraph(
            escape(
                f"{labels['grade']} {exam['grade']} | {labels['subject']}: {exam['subject']} | "
                f"{exam['total_marks']} {labels['marks']} | "
                f"{exam['duration_minutes']} {labels['duration']}"
            ),
            body_style,
        ),
    ]
    if answer_key:
        story.append(Paragraph(escape(labels["teacher_copy"]), body_style))
    else:
        story.append(Paragraph(escape(labels["student_info"]), body_style))
        story.append(Paragraph(escape(labels["instructions"]), body_style))
    for number, question in enumerate(exam["questions"], start=1):
        story.append(
            Paragraph(
                escape(f"{number}. [{question['marks']} {labels['marks']}] {question['text']}"),
                body_style,
            )
        )
        if answer_key:
            story.append(Paragraph(escape(f"{labels['answer']}: {question['answer']}"), body_style))
            for label_key, key in (("explanation", "explanation"), ("rubric", "rubric")):
                if question.get(key):
                    story.append(Paragraph(escape(f"{labels[label_key]}: {question[key]}"), body_style))
        else:
            for index, option in enumerate(question.get("options", [])):
                story.append(Paragraph(escape(f"{chr(65 + index)}. {option}"), body_style))
            if question["type"] in {"Short Answer", "Essay", "Problem Solving"}:
                story.append(Spacer(1, 36))
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48
    )
    document.build(story)
    return output.getvalue()


def export_exam(exam: dict, file_format: str, document_type: str) -> tuple[bytes, str, str]:
    _is_answer_key(document_type)
    safe_title = "".join(
        character if character.isalnum() or character in "-_" else "_" for character in exam["title"]
    ).strip("_") or "exam"
    suffix = "answer-key" if document_type == "answer_key" else "paper"
    if file_format == "docx":
        return _docx(exam, document_type), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", f"{safe_title}-{suffix}.docx"
    if file_format == "pdf":
        return _pdf(exam, document_type), "application/pdf", f"{safe_title}-{suffix}.pdf"
    raise ValueError("File format must be pdf or docx.")


def content_disposition(filename: str) -> str:
    fallback = "".join(
        character
        if (character.isascii() and character.isalnum()) or character in "-_."
        else "_"
        for character in filename
    )
    return f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(filename)}'
