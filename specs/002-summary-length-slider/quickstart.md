# Quickstart: Summary Length Slider

**Feature Branch**: `002-summary-length-slider`
**Date**: 2026-02-07
**Depends On**: Feature 001 (YouTube Video Summary) must be implemented first.

## What's New

A slider control that lets you choose how long the summary should be, from 10% to 50% of the original transcript's word count. The default is 25%.

## Setup

No additional setup needed beyond what feature 001 requires. No new dependencies or environment variables.

## Usage

1. Open `http://localhost:5173` in your browser.
2. Adjust the **Summary Length** slider to your preferred percentage (10%–50%).
3. Paste a YouTube video URL into the input field.
4. Click "Summarize" and wait for the summary to appear.

The slider value is shown as a percentage label (e.g., "25%"). Moving the slider updates the label in real time.

## API Changes

The `POST /api/summarize` endpoint now accepts an optional `length_percent` field:

### Example Request (custom length)

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "length_percent": 10}'
```

### Example Request (default length, backward-compatible)

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Allowed Values

| Parameter | Type | Required | Range | Step | Default |
|-----------|------|----------|-------|------|---------|
| `length_percent` | integer | No | 10–50 | 5 | 25 |

## Running Tests

Same as feature 001:

```bash
# Backend
cd backend && source .venv/bin/activate
pytest tests/

# Frontend
cd frontend
npm run test
```
