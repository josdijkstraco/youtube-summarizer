# Quickstart: Fallacy Analysis

**Feature Branch**: `003-fallacy-analysis`
**Date**: 2026-02-07
**Depends On**: Features 001 (YouTube Video Summary) and 002 (Summary Length Slider) must be implemented first.

## What's New

The summarization response now automatically includes a logical fallacy analysis of the transcript. Each identified fallacy includes the quoted passage, fallacy name, category, severity rating, explanation, and an illustrative example. Fallacies are displayed with color-coded severity indicators (red = high, amber = medium, yellow = low) and a summary statistics panel.

## Setup

No additional setup needed beyond what features 001 and 002 require. No new dependencies or environment variables.

## Usage

1. Open `http://localhost:5173` in your browser.
2. Paste a YouTube video URL into the input field.
3. Optionally adjust the **Summary Length** slider.
4. Click "Summarize" and wait for the results.
5. Below the summary, view the **Fallacy Analysis** section showing:
   - A statistics panel with total count, severity breakdown, and primary tactics
   - Individual fallacy cards color-coded by severity

## API Changes

The `POST /api/summarize` response now includes an optional `fallacy_analysis` field:

### Example Response (with fallacies found)

```json
{
  "summary": "This video discusses...",
  "metadata": { "video_id": "...", "title": "...", ... },
  "fallacy_analysis": {
    "summary": {
      "total_fallacies": 2,
      "high_severity": 1,
      "medium_severity": 1,
      "low_severity": 0,
      "primary_tactics": ["Ad Hominem", "Straw Man"]
    },
    "fallacies": [
      {
        "timestamp": null,
        "quote": "You can't trust him because...",
        "fallacy_name": "Ad Hominem",
        "category": "Relevance",
        "severity": "high",
        "explanation": "This attacks the person rather than...",
        "clear_example": {
          "scenario": "Dismissing a mechanic's diagnosis because...",
          "why_wrong": "Expertise comes from experience, not..."
        }
      }
    ]
  }
}
```

### Example Response (no fallacies found)

```json
{
  "summary": "This video discusses...",
  "metadata": { ... },
  "fallacy_analysis": {
    "summary": {
      "total_fallacies": 0,
      "high_severity": 0,
      "medium_severity": 0,
      "low_severity": 0,
      "primary_tactics": []
    },
    "fallacies": []
  }
}
```

### Example Response (fallacy analysis failed)

```json
{
  "summary": "This video discusses...",
  "metadata": { ... },
  "fallacy_analysis": null
}
```

The request format is unchanged — no new parameters needed.

## Running Tests

Same as previous features:

```bash
# Backend
cd backend && source .venv/bin/activate
pytest tests/

# Frontend
cd frontend
npm run test
```
