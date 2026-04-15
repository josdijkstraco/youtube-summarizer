# YouTube Summarizer 4.6 — Wiki Index

A full-stack platform that fetches YouTube transcripts and uses OpenAI to summarize them, detect logical fallacies, and answer questions about the content.

## Quick Start

```bash
# Docker (production-like)
docker-compose up -d --build
# Frontend → http://localhost:3002
# Backend  → http://localhost:8002

# Local development
cd backend && uvicorn app.main:app --reload --port 8002
cd frontend && npm run dev          # http://localhost:5173

# Tests & lint
cd backend && pytest
cd backend && ruff check .
cd frontend && npm run lint
```

---

## Pages

| Page | What's inside |
|------|---------------|
| [architecture.md](architecture.md) | System diagram, tech stack, key data flows, caching strategy |
| [api-endpoints.md](api-endpoints.md) | Every REST endpoint — method, path, request, response, errors |
| [backend-services.md](backend-services.md) | Summarizer, fallacy analyzer, Q&A, transcript, YouTube services |
| [database.md](database.md) | Table schema, all `db.py` functions, soft-delete, highlight merge |
| [data-models.md](data-models.md) | Pydantic models, TypeScript interfaces, backend ↔ frontend mapping |
| [frontend.md](frontend.md) | Component tree, App.vue state, SummaryDisplay tabs, API service |
| [deployment.md](deployment.md) | Docker Compose, env vars, cookies.txt, local dev setup |
| [wiki.md](wiki.md) | Glossary of terms used throughout the project |

---

## Source File Map

### Backend
| File | Purpose |
|------|---------|
| [`backend/app/main.py`](../backend/app/main.py) | FastAPI app — all 11 endpoints |
| [`backend/app/models.py`](../backend/app/models.py) | Pydantic request/response models |
| [`backend/app/db.py`](../backend/app/db.py) | PostgreSQL functions (asyncpg) |
| [`backend/app/config.py`](../backend/app/config.py) | Settings loaded from `.env` |
| [`backend/app/services/summarizer.py`](../backend/app/services/summarizer.py) | OpenAI summarization + chunking |
| [`backend/app/services/fallacy_analyzer.py`](../backend/app/services/fallacy_analyzer.py) | Logical fallacy detection via OpenAI |
| [`backend/app/services/qa.py`](../backend/app/services/qa.py) | Q&A via gpt-4o with transcript context |
| [`backend/app/services/transcript.py`](../backend/app/services/transcript.py) | YouTube transcript fetching |
| [`backend/app/services/youtube.py`](../backend/app/services/youtube.py) | Video ID extraction, oEmbed metadata |

### Frontend
| File | Purpose |
|------|---------|
| [`frontend/src/App.vue`](../frontend/src/App.vue) | Root component — all top-level state |
| [`frontend/src/components/SummaryDisplay.vue`](../frontend/src/components/SummaryDisplay.vue) | Tabbed UI (summary / transcript / Q&A / notes) |
| [`frontend/src/components/HistoryPanel.vue`](../frontend/src/components/HistoryPanel.vue) | Sidebar history drawer |
| [`frontend/src/components/HistoryCard.vue`](../frontend/src/components/HistoryCard.vue) | Individual history entry |
| [`frontend/src/components/FallacyDisplay.vue`](../frontend/src/components/FallacyDisplay.vue) | Fallacy table with expandable rows |
| [`frontend/src/components/FallacySummaryPanel.vue`](../frontend/src/components/FallacySummaryPanel.vue) | Fallacy severity stats panel |
| [`frontend/src/components/UrlInput.vue`](../frontend/src/components/UrlInput.vue) | URL input + submit |
| [`frontend/src/components/LengthSlider.vue`](../frontend/src/components/LengthSlider.vue) | Summary length slider (10–50%) |
| [`frontend/src/services/api.ts`](../frontend/src/services/api.ts) | All API calls + `ApiError` class |
| [`frontend/src/types/index.ts`](../frontend/src/types/index.ts) | TypeScript interfaces |

### Config & Infra
| File | Purpose |
|------|---------|
| [`docker-compose.yml`](../docker-compose.yml) | Docker services (backend :8002, frontend :3002) |
| [`backend/.env.example`](../backend/.env.example) | Required environment variables |
| [`backend/requirements.txt`](../backend/requirements.txt) | Python dependencies |
| [`frontend/package.json`](../frontend/package.json) | Node dependencies & scripts |
| [`cookies.txt`](../cookies.txt) | Optional YouTube auth cookies (Netscape format) |
