# Deployment

## Docker Compose (Recommended)

**File:** [`docker-compose.yml`](../docker-compose.yml)

```bash
docker-compose up -d --build
```

| Service | Internal port | Host port | URL |
|---------|--------------|-----------|-----|
| `backend` | 8002 | 8002 | http://localhost:8002 |
| `frontend` | 80 (nginx) | 3002 | http://localhost:3002 |

### Services

**backend**
- Built from `./backend/Dockerfile` (Python 3.12 slim)
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8002`
- Loads env from `./backend/.env`
- Volumes:
  - `./data:/app/data` — data directory
  - `./cookies.txt:/app/cookies.txt:ro` — optional YouTube auth cookies

**frontend**
- Built from `./frontend/Dockerfile` (Node build → nginx)
- `VITE_API_URL` build arg: `http://localhost:8002`
- `depends_on: backend`

---

## Environment Variables

Create `backend/.env`:

```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

| Variable | Required | Notes |
|----------|----------|-------|
| `OPENAI_API_KEY` | yes | OpenAI API key |
| `DATABASE_URL` | yes | PostgreSQL DSN. Format: `postgresql://user:pass@host:5432/db` |
| `BACKEND_CORS_ORIGINS` | no | JSON array. Default: `["http://localhost:5173", "http://localhost:3002"]` |

The database schema (`youtube_summarizer.summaries`) is created automatically on first startup via `create_table()` in `db.py`. **The `youtube_summarizer` schema must already exist** in the database before startup:

```sql
CREATE SCHEMA IF NOT EXISTS youtube_summarizer;
```

---

## YouTube Cookie Authentication

YouTube occasionally blocks transcript fetching from server IPs. The app supports cookie-based authentication as a fallback.

**Setup:**
1. Export your YouTube cookies from a browser using a Netscape-format cookie exporter (e.g., the "Get cookies.txt LOCALLY" extension).
2. Save the file to `cookies.txt` in the project root.
3. The file is mounted read-only into the backend container at `/app/cookies.txt`.

The transcript service checks for `/app/cookies.txt` at runtime:
```python
COOKIES_PATH = "/app/cookies.txt"
```
If the file exists, a `requests.Session` with those cookies is passed to `YouTubeTranscriptApi`.

---

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create backend/.env with OPENAI_API_KEY and DATABASE_URL
uvicorn app.main:app --reload --port 8002
```

API available at `http://localhost:8002`.  
Auto-reloads on file changes with `--reload`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server at `http://localhost:5173` with Hot Module Replacement.

Set `VITE_API_URL` in `frontend/.env.local` if your backend runs on a different port:
```bash
VITE_API_URL=http://localhost:8002
```

### Tests & Lint

```bash
# Backend
cd backend
pytest                  # run all tests
ruff check .            # lint
mypy app/               # type-check

# Frontend
cd frontend
npm run test            # Vitest unit tests
npm run lint            # ESLint + Prettier
```

---

## Database Setup

The app assumes PostgreSQL is available externally (AWS RDS, self-hosted, or local Docker).

```bash
# Local PostgreSQL via Docker
docker run -d \
  --name yt-db \
  -e POSTGRES_USER=yt \
  -e POSTGRES_PASSWORD=yt \
  -e POSTGRES_DB=yt \
  -p 5432:5432 \
  postgres:16

# Create the schema
psql postgresql://yt:yt@localhost:5432/yt -c "CREATE SCHEMA IF NOT EXISTS youtube_summarizer;"
```

Then set `DATABASE_URL=postgresql://yt:yt@localhost:5432/yt` in `.env`.

The table is created automatically on first startup.
