# Khmer ExamGen AI

A teacher-reviewed exam generator with a React dashboard and a FastAPI backend. Uploaded lesson files are extracted and used as the primary source for AI-generated questions. The service stores lesson text and exams in SQLite and exports student papers and answer keys separately.

## Architecture

```text
frontend/                 React + Vite + Tailwind teacher dashboard
backend/app/main.py       FastAPI application and HTTP routes
backend/app/database.py   SQLite persistence for lessons and exams
backend/app/documents.py  PDF, DOCX, PPTX, and TXT extraction
backend/app/generator.py  OpenAI-compatible LLM integration and validation
backend/app/exporters.py  DOCX and PDF generation
```

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

1. Start the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   # Set LLM_API_KEY in .env to enable AI generation
   uvicorn app.main:app --reload
   ```

2. In another terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open the Vite URL (normally http://localhost:5173). The frontend proxies `/api` requests to `http://localhost:8000`.

The API documentation is available at http://localhost:8000/docs. Without an LLM API key, uploading, saving, editing, and exporting still work; generation returns a clear configuration error rather than sample or fabricated content.

## AI configuration

Set `LLM_API_KEY`, `LLM_MODEL`, and optionally `LLM_BASE_URL` in `backend/.env`. The default endpoint is OpenAI's chat-completions API; any compatible endpoint can be configured, including an OpenAI-compatible gateway for a Khmer-capable model. Set `LLM_MODEL` to the model you have access to. The model is instructed to produce Khmer by default and to use only the uploaded lesson.

## Khmer exports

DOCX files declare **Noto Sans Khmer** as the font. For PDF output, set `KHMER_FONT_PATH` to an installed Khmer TrueType font file (for example, Noto Sans Khmer Regular). The exporter also checks common Windows font locations. Install a font if the PDF viewer does not render Khmer glyphs correctly.

## Workflow

1. Upload a lesson as PDF, DOCX, PPTX, or TXT.
2. Set grade, subject, exam title, marks, duration, question count, difficulty, types, and output language.
3. Generate an exam from the selected lesson. The backend validates the response, assigns integer marks whose total matches the configured score, and saves the exam.
4. Review and edit questions. Regenerate a question or answer key after changes.
5. Download the student paper and answer key independently as DOCX or PDF.

Generated content is a draft for teacher review and approval. The system does not create textbook citations or curriculum references.
