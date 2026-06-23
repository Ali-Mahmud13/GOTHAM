# GOTHAM

GOTHAM is a clinical support prototype for maternal and fetal health workflows. It combines a FastAPI backend, a React/Vite frontend, patient and appointment management, voice transcription, LLM-assisted chat, RAG retrieval, and ML-based risk assessment pipelines.

## Project Structure

```text
.
|-- backend/                 # FastAPI app, SQLModel models, API routers, Alembic migrations
|-- frontend/                # Vite + React + TypeScript UI
|-- data/                    # Local data assets
|-- docs/                    # Project notes, security notes, evaluation docs
|-- models/                  # Model assets
|-- notebooks/               # Experiments and exploratory work
|-- config.py                # Root RAG/model configuration
`-- requirements.txt         # Python backend and ML dependencies
```

## Main Features

- Doctor and patient authentication with JWT access and refresh tokens.
- Patient records, visit notes, assessments, and patient portal endpoints.
- Appointment booking, doctor availability, registration requests, and notification flows.
- Clinical note parsing and chat endpoints backed by configurable LLM providers.
- Maternal and fetal health assessment pipelines for GDM, anemia, preeclampsia, CTG, and ultrasound workflows.
- RAG ingestion and retrieval using Pinecone and sentence-transformer embeddings.
- Speech-to-text transcription using Groq Whisper with local faster-whisper fallback.
- React dashboard and patient/doctor pages built with shadcn-style components.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- PostgreSQL-compatible database URL, such as Neon
- Optional API keys for OpenAI, Groq, Gemini, Pinecone, Hugging Face, and Cloudinary depending on the features you run

## Backend Setup

Create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root or backend environment with the values needed by the app. Use placeholder values like these; do not commit or share real credentials:

```env
# Database
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
TEST_DATABASE_URL=sqlite:///./test.db

# App
DEBUG=false
JWT_SECRET=replace-with-a-long-random-secret
JWT_ACCESS_MINUTES=1440
JWT_REFRESH_DAYS=30
ALLOW_LEGACY_PASSWORD_HASH=true
ALLOW_LEGACY_HEADER_AUTH=false
CORS_ALLOWED_ORIGINS=http://localhost:5173
RATE_LIMIT_ENABLED=true

# Inngest
INNGEST_APP_ID=GOTHAM
INNGEST_EVENT_KEY=local-dev-key
INNGEST_EVENT_API_BASE_URL=http://localhost:8288

# LLM provider: openai, groq, or gemini
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL_NAME=gpt-4o-mini

GROQ_API_KEY=
MODEL_NAME=llama-3.3-70b-versatile

GEMINI_API_KEY=
GEMINI_MODEL_NAME=gemini-1.5-flash
EXTRACTION_MODEL=

# Speech-to-text
STT_PROVIDER=auto
GROQ_WHISPER_MODEL=whisper-large-v3
WHISPER_MODEL=large-v3-turbo
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
TRANSCRIBE_MAX_BYTES=26214400

# RAG / vector search
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX_NAME=rag-fyp-medical
HUGGINGFACEHUB_API_TOKEN=

# Cloudinary uploads
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=gotham
CLOUDINARY_PUBLIC_URLS=true

# Diagnostics
BENCHMARK=false
RESPONSE_CACHE=true
```

Run database migrations from the backend directory:

```powershell
cd backend
alembic upgrade head
```

Start the API server:

```powershell
uvicorn app.main:app --reload
```

The backend exposes health and API documentation at:

- `http://localhost:8000/health`


## Frontend Setup

Install frontend dependencies and start the development server:

```powershell
cd frontend
npm install
npm run dev
```

The Vite app usually runs at `http://localhost:5173`.

## Common Commands

Initialize the database:

```bash
python scripts/init_db.py
```

## Running

### 1. Start FastAPI

```bash
cd backend

# Linux/macOS
INNGEST_DEV=1 uvicorn app.main:app --reload --reload-exclude="*.pyc" --reload-exclude="*.pth" --reload-exclude="*.pt" --reload-exclude="__pycache__"

# Windows (PowerShell)
$env:INNGEST_DEV=1; uvicorn app.main:app --reload --reload-exclude="*.pyc" --reload-exclude="*.pth" --reload-exclude="*.pt" --reload-exclude="__pycache__"
```


### 2. Start Inngest Dev Server (new terminal)

```bash
npx inngest-cli@latest dev
or
install -g inngest-cli
inngest dev
or npx inngest-cli@latest dev -u http://localhost:8000/api/inngest  #to auto sync

### 3. Frontend
cd frontend 
npm run dev

## Notes

- `DATABASE_URL` is required outside of pytest. Tests default to SQLite through `TEST_DATABASE_URL` or `sqlite:///./test.db`.
- `JWT_SECRET` is required when `DEBUG=false`.
- Local faster-whisper models are downloaded on first use and may require significant disk space.
- Some ML and RAG features depend on model files and external service keys being present.
