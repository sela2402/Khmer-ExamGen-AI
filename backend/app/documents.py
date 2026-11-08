from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document
from pptx import Presentation


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}


def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a PDF, DOCX, PPTX, or TXT file.")

    try:
        if extension == ".pdf":
            with pymupdf.open(stream=content, filetype="pdf") as document:
                sections = [page.get_text("text") for page in document]
        elif extension == ".docx":
            document = Document(BytesIO(content))
            sections = [paragraph.text for paragraph in document.paragraphs]
            sections.extend(
                cell.text
                for table in document.tables
                for row in table.rows
                for cell in row.cells
            )
        elif extension == ".pptx":
            presentation = Presentation(BytesIO(content))
            sections = []
            for slide_number, slide in enumerate(presentation.slides, start=1):
                slide_text = [
                    shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False)
                ]
                slide_text.extend(
                    cell.text
                    for shape in slide.shapes
                    if getattr(shape, "has_table", False)
                    for row in shape.table.rows
                    for cell in row.cells
                )
                sections.append(f"Slide {slide_number}\n" + "\n".join(slide_text))
        else:
            sections = [content.decode("utf-8-sig")]
    except (UnicodeDecodeError, pymupdf.FileDataError, KeyError) as error:
        raise ValueError("The uploaded file could not be read. Check that it is a valid document.") from error
    except Exception as error:
        raise ValueError("The uploaded file could not be read. Check that it is a valid document.") from error

    text = "\n\n".join(section.strip() for section in sections if section.strip()).strip()
    if not text:
        raise ValueError("No readable text was found in the document.")
    return text
