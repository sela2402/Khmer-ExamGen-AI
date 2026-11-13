# Khmer ExamGen AI

A teacher-reviewed exam generator with a React dashboard and a FastAPI backend. Uploaded lesson files are extracted and used as the primary source for AI-generated questions. The service stores lesson text and exams in Supabase PostgreSQL when `DATABASE_URL` is configured, and otherwise uses SQLite for local development. Student papers and answer keys are exported separately.

## Architecture

```text
frontend/                 React + Vite + Tailwind teacher dashboard
backend/app/main.py       FastAPI application and HTTP routes
backend/app/database.py   SQLAlchemy PostgreSQL/SQLite persistence for lessons and exams
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
   # Set DATABASE_URL to use Supabase PostgreSQL and LLM_API_KEY to enable AI generation
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

Email and password sign-up and login use Supabase Auth; credentials are stored in Supabase's `auth.users`, not in the application's lessons/exams database. In the Supabase dashboard, go to **Authentication → Sign In / Providers → Email**, enable Email, and turn **Confirm email** off for development. Set **Site URL** to `http://localhost:5173`.

Configure these values in `backend/.env`:

```text
SUPABASE_URL=https://slehhdvtfivgcuaguvib.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env` using the same project URL and publishable key. These frontend variables are public by design; never use a Supabase service-role/secret key in the browser. The backend verifies each bearer token with Supabase Auth's `get_user` endpoint.

`GET /me` returns the authenticated user's ID and email. Authentication is required for:

- `GET /me`
- `GET /api/lessons`, `POST /api/lessons`, `DELETE /api/lessons/{lesson_id}`
- `GET /api/exams`, `POST /api/chat`, `POST /api/exams/generate`
- `GET /api/exams/{exam_id}`, `PUT /api/exams/{exam_id}`, `DELETE /api/exams/{exam_id}`
- `POST /api/exams/{exam_id}/questions/regenerate`
- `POST /api/exams/{exam_id}/answer-key/regenerate`
- `GET /api/exams/{exam_id}/export`

`GET /api/health` remains public. Lessons and exams are isolated by authenticated user. In SQLite, rows without an owner remain stored but are hidden from all users; assign an owner manually before making legacy rows available.

To run and test the authentication flow:

1. In `backend/.env`, set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and (if using PostgreSQL storage) `DATABASE_URL`.
2. In `frontend/.env`, set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
3. Start the backend in PowerShell:

   ```powershell
   cd backend
   if (!(Test-Path .env)) { Copy-Item .env.example .env }
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. In another terminal, start the frontend:

   ```powershell
   cd frontend
   if (!(Test-Path .env)) { Copy-Item .env.example .env }
   npm install
   npm run dev
   ```

5. Open `http://localhost:5173`, choose **Sign up**, and register with an email and password of at least six characters. With email confirmation disabled, the new account should be signed in immediately. Verify it under **Authentication → Users** in Supabase.
6. Log out, then log back in with the same credentials.
7. In the browser developer console, get the current access token with:

   ```js
   const { data } = await (await import("/src/supabaseClient.js")).supabase.auth.getSession();
   data.session.access_token
   ```

   Call `/me` from PowerShell, replacing the placeholder with that token:

   ```powershell
   $token = "PASTE_ACCESS_TOKEN_HERE"
   Invoke-RestMethod -Uri "http://localhost:8000/me" -Headers @{ Authorization = "Bearer $token" }
   ```

   The response should contain the signed-in user's `id` and `email`.

## Supabase database

Set `DATABASE_URL` in `backend/.env` to the Supabase transaction-mode pooler connection string (port `6543`) shown in `backend/.env.example`. Replace `YOUR-PASSWORD` with the database password; percent-encode special characters in the password before putting it in the URL. The SQLAlchemy engine enables SSL and disables prepared statements for compatibility with transaction pooling. Keep this connection string server-side; do not put it in `frontend/.env` or commit it. Existing SQLite data is not copied automatically. If `DATABASE_URL` is unset, the backend uses SQLite for local development. This backend initializes its schema at startup and does not currently use a separate migration URL.

## AI configuration

Set `LLM_API_KEY`, `LLM_MODEL`, and optionally `LLM_BASE_URL` in `backend/.env`. The default endpoint is OpenAI's chat-completions API; any compatible endpoint can be configured, including an OpenAI-compatible gateway for a Khmer-capable model. Set `LLM_MODEL` to the model you have access to. The model is instructed to produce Khmer by default and to use only the uploaded lesson.

## Supabase client

The frontend exports a Supabase client from `frontend/src/supabaseClient.js`. Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `frontend/.env` (see `frontend/.env.example`). These Vite variables are public in the browser; protect directly exposed tables with appropriate Supabase Row Level Security policies. Lesson and exam data is accessed through the FastAPI backend and stored in PostgreSQL when `DATABASE_URL` is configured.

## Khmer exports

DOCX files declare **Noto Sans Khmer** as the font. For PDF output, set `KHMER_FONT_PATH` to an installed Khmer TrueType font file (for example, Noto Sans Khmer Regular). The exporter also checks common Windows font locations. Install a font if the PDF viewer does not render Khmer glyphs correctly.

## Workflow

1. Upload a lesson as PDF, DOCX, PPTX, or TXT. Uploaded lessons can be deleted from the lesson library; existing exams remain, but cannot use the deleted lesson for regeneration.
2. Set grade, subject, exam title, marks, duration, question count, difficulty, types, and output language.
3. Generate an exam from the selected lesson. The backend validates the response, assigns integer marks whose total matches the configured score, and saves the exam.
4. Review and edit questions, or delete an examination from the recent-exams list. Regenerate a question or answer key after changes.
5. Download the student paper and answer key independently as DOCX or PDF.

Generated content is a draft for teacher review and approval. The system does not create textbook citations or curriculum references.
