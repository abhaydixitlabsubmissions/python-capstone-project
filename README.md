# BookMind 🧠📚

A multi-user AI book and knowledge platform with intelligent ingestion, citations-grounded RAG, structured notes, and personal library discovery.

## Features

- 📖 **Intelligent Book Ingestion**: Upload PDF, EPUB, and DOCX documents with chapter/section detection and smart hierarchical chunking.
- ⚡ **Exact & Semantic Deduplication**: SHA-256 hash checking and vector similarity detection against your personal library before processing.
- 💬 **Context-Grounded Chat (RAG)**: Chat with any book with streaming responses and exact page-level citations.
- 📝 **Structured Notes & Summaries**: Generate chapter summaries, study notes, and save chat responses directly to editable notes (Tiptap).
- 🔍 **Personal Document Discovery**: Find related books and ideas across your own library.

## Architecture

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), pgvector, Pydantic v2
- **Workers**: Celery + Redis for asynchronous document ingestion & embedding generation
- **Database**: PostgreSQL 16 with `pgvector` extension

## Quickstart

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env with your OpenAI or Gemini API keys
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```

Services will be available at:
- **Frontend**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
