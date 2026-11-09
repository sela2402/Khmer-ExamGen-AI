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

3. To use the optional Streamlit interface alongside or instead of React, install the backend requirements and start it in another terminal:

   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

   The Streamlit interface uses the same FastAPI service and database. Set `EXAMGEN_API_URL` if the API is not at `http://127.0.0.1:8000`.

The API documentation is available at http://localhost:8000/docs. Without an LLM API key, uploading, saving, editing, and exporting still work; generation returns a clear configuration error rather than sample or fabricated content.

## Supabase authentication

The React and Streamlit interfaces sign in with Supabase Auth. Create teacher accounts in the Supabase project's Auth users settings, enable the email/password provider, and configure these backend values in `backend/.env`:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-publishable-key
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
```

Set the matching `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env`. The API validates bearer access tokens against the project's JWKS and requires authentication for every API route except `/api/health`. Lessons and exams are isolated by authenticated user. Existing SQLite rows without an owner remain stored but are hidden from all users; assign an owner manually before making legacy rows available. Keep any Supabase secret key server-side; it is not needed for this JWT verification flow and must never be placed in frontend variables.

## AI configuration

Set `LLM_API_KEY`, `LLM_MODEL`, and optionally `LLM_BASE_URL` in `backend/.env`. The default endpoint is OpenAI's chat-completions API; any compatible endpoint can be configured, including an OpenAI-compatible gateway for a Khmer-capable model. Set `LLM_MODEL` to the model you have access to. The model is instructed to produce Khmer by default and to use only the uploaded lesson.

## Supabase client

The frontend exports a Supabase client from `frontend/src/utils/supabase.js`. Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env` (see `frontend/.env.example`). These Vite variables are public in the browser; protect tables with appropriate Supabase Row Level Security policies. The app's lesson and exam data continues to use the FastAPI/SQLite backend.

## Khmer exports

DOCX files declare **Noto Sans Khmer** as the font. For PDF output, set `KHMER_FONT_PATH` to an installed Khmer TrueType font file (for example, Noto Sans Khmer Regular). The exporter also checks common Windows font locations. Install a font if the PDF viewer does not render Khmer glyphs correctly.

## Workflow

1. Upload a lesson as PDF, DOCX, PPTX, or TXT. Uploaded lessons can be deleted from the lesson library; existing exams remain, but cannot use the deleted lesson for regeneration.
2. Set grade, subject, exam title, marks, duration, question count, difficulty, types, and output language.
3. Generate an exam from the selected lesson. The backend validates the response, assigns integer marks whose total matches the configured score, and saves the exam.
4. Review and edit questions, or delete an examination from the recent-exams list. Regenerate a question or answer key after changes.
5. Download the student paper and answer key independently as DOCX or PDF.

Generated content is a draft for teacher review and approval. The system does not create textbook citations or curriculum references.
