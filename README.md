# Study Companion — AI-Powered Study Buddy (MVP V1)

A production-structured Django web application that helps school students study smarter using RAG (Retrieval-Augmented Generation), document upload, adaptive re-explanation, and auto-generated study materials.

## Features

| Feature | Description |
|---------|-------------|
| **Authentication** | Sign up, log in, log out (session-based) |
| **Document Upload** | PDF or pasted text notes → extract, chunk, embed, FAISS index |
| **AI Study Chat** | Ask questions grounded in uploaded material |
| **"I Don't Understand"** | Simpler re-explanations with analogies, steps, and confusion checkpoints |
| **Auto Generation** | Revision notes, summaries, MCQ quizzes |
| **Progress Tracking** | Questions asked, quiz scores, weak topic identification |

## Tech Stack

- **Backend:** Python, Django 5, Django REST Framework
- **Frontend:** Django templates + TailwindCSS (CDN)
- **Database:** SQLite
- **AI/NLP:** sentence-transformers, FAISS, OpenAI-compatible API (optional)
- **PDF Parsing:** PyMuPDF
- **Deployment:** Docker + Gunicorn + WhiteNoise

## Project Structure

```
study_companion/
├── config/              # Django settings, URLs, WSGI
├── apps/
│   ├── accounts/        # Auth views & forms
│   ├── documents/       # Upload, models, API
│   ├── study/           # Chat, generation, materials
│   └── progress/        # Analytics, quiz attempts
├── services/            # Business logic layer
│   ├── document_service.py
│   ├── rag_service.py
│   ├── generation_service.py
│   └── progress_service.py
├── ai/                  # RAG pipeline
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── llm.py
│   └── prompts.py
├── templates/           # HTML templates
├── static/              # CSS
├── media/               # Uploaded files (runtime)
└── vector_stores/       # FAISS indexes (runtime)
```

## Quick Start (Local)

### 1. Prerequisites

- Python 3.11+ (3.12 recommended)
- pip

### 2. Setup

```bash
cd study_companion
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Configure (optional)

Edit `.env` to add an OpenAI-compatible API key for higher-quality AI responses:

```
OPENAI_API_KEY=sk-your-key-here
```

Without an API key, the app uses a **grounded fallback mode** that builds answers directly from retrieved document chunks.

### 4. Run migrations & start server

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for admin
python manage.py runserver
```

Open **http://127.0.0.1:8000/**

### 5. Try the demo flow

1. Sign up for an account
2. Go to **Upload** → choose "Text Notes" → paste content from `sample_notes/biology_photosynthesis.txt`
3. Wait for processing (status: Ready)
4. Click **Start Study Chat** and ask: *"What is photosynthesis?"*
5. Click **I still don't understand** for a simpler explanation
6. Generate **Notes**, **Summary**, or **Quiz** from the document detail page
7. View **Progress** analytics

## Docker

```bash
cp .env.example .env
docker compose up --build
```

App runs at **http://localhost:8000**

## API Endpoints (DRF)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/` | List user documents |
| GET | `/api/study/materials/` | List generated materials |
| POST | `/api/study/chat/<id>/ask/` | Ask a question `{"question": "..."}` |
| POST | `/api/study/chat/<id>/reexplain/` | Re-explain `{"message_id": 1}` |
| GET | `/api/progress/summary/` | Progress summary |
| POST | `/api/progress/quiz/<id>/submit/` | Submit quiz answers |

All API routes require session authentication (log in via browser first).

## RAG Pipeline

```
Upload → PyMuPDF/text extract → Chunk → Embed (MiniLM) → FAISS index
                                                              ↓
User question → Embed query → FAISS search → Top-K chunks → LLM prompt → Answer
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (dev key) | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `OPENAI_API_KEY` | (empty) | LLM API key (optional) |
| `OPENAI_BASE_URL` | OpenAI URL | Compatible API base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `80` | Chunk overlap |
| `TOP_K_CHUNKS` | `5` | Retrieved chunks for RAG |

## Architecture Notes

- **Service layer** (`services/`) keeps views thin and logic testable
- **AI layer** (`ai/`) isolates embeddings, vector search, and LLM calls
- **Per-document FAISS indexes** stored on disk for simplicity (upgrade path: shared vector DB)
- **Grounded fallback** ensures demo functionality without external API costs

## License

Educational / demonstration project.
