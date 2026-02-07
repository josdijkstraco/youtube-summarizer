# Quickstart: YouTube Video Summary

**Feature Branch**: `001-video-summary`
**Date**: 2026-02-06

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- An OpenAI API key (for GPT-4o-mini summarization)

## Setup

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Run the development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit
`http://localhost:8000/docs` for interactive API documentation.

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Usage

1. Open `http://localhost:5173` in your browser.
2. Paste a YouTube video URL into the input field.
3. Click "Summarize" and wait for the summary to appear.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for GPT-4o-mini |

## Running Tests

### Backend

```bash
cd backend
pytest                    # Run all tests
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
```

### Frontend

```bash
cd frontend
npm run test              # Run all tests
npm run test:unit         # Unit tests only
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/summarize` | Submit a YouTube URL for summarization |
| GET | `/api/health` | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Example Response

```json
{
  "summary": "This video covers the key topics of...",
  "metadata": {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "channel_name": "Channel Name",
    "duration_seconds": 600,
    "thumbnail_url": "https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg"
  }
}
```
