# Quickstart: Postgres Video Storage (004)

## Prerequisites

- An AWS RDS PostgreSQL instance (or compatible managed Postgres) already provisioned and reachable from your development machine or deployment host
- Python 3.13 with the backend virtualenv active
- Node 18+ with the frontend deps installed

---

## 1. Add the database dependency

```bash
cd backend
pip install asyncpg>=0.30.0
# Then add to requirements.txt:
echo "asyncpg>=0.30.0" >> requirements.txt
```

---

## 2. Configure the connection string

Add to `backend/.env`:

```env
DATABASE_URL=postgresql://your_user:your_password@your-rds-host.amazonaws.com:5432/youtube_summarizer
```

The table (`summaries`) is created automatically on first startup via `CREATE TABLE IF NOT EXISTS`. No migration tool is needed.

---

## 3. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

On startup you should see the pool initialising. If `DATABASE_URL` is missing or malformed, the app will fail immediately with a Pydantic validation error — check your `.env` file.

---

## 4. Verify connectivity

```bash
curl http://localhost:8000/api/history
# Expected: {"items": []}
```

---

## 5. Test the full flow

Submit a video URL. The response is returned as before. Check that the record was stored:

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Then verify storage:
curl http://localhost:8000/api/history
# Should contain the video you just processed.

# Submit the same URL again — should be instant (cache hit):
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## 6. Frontend

The history panel appears automatically as a left sidebar when the backend returns results from `/api/history`. No additional configuration is required.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ValidationError: database_url` at startup | `DATABASE_URL` missing from `.env` | Add the env var and restart |
| `asyncpg.InvalidPasswordError` | Wrong credentials in `DATABASE_URL` | Check `backend/.env` |
| `asyncpg.CannotConnectNowError` | RDS host unreachable | Check VPC/security group rules; ensure your IP is whitelisted |
| History panel shows "Could not load history" | Backend not running or CORS misconfigured | Confirm `uvicorn` is running on port 8000 |
| `storage_warning: true` in summarize response | Postgres unreachable at persist time | Summary is still returned; check DB connectivity |
