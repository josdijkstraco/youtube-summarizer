# Backend Services

Business logic lives in [`backend/app/services/`](../backend/app/services/). Each service is a standalone module with no cross-service imports.

---

## summarizer.py

**File:** [`backend/app/services/summarizer.py`](../backend/app/services/summarizer.py)
**Model:** `gpt-4o-mini`
**Timeout:** 30s per API call

### Main function

```python
def generate_summary(
    transcript_text: str,
    *,
    transcript_word_count: int | None = None,
    length_percent: int | None = None,
) -> SummaryResult
```

Returns `SummaryResult(content, total_prompt_tokens, total_completion_tokens)`.

### Algorithm

1. Build system prompt. If `length_percent` is provided, append a length instruction:
   `"Your summary should be approximately N words (about X% of the transcript)."`
   where `N = transcript_word_count * length_percent // 100`.

2. **Short transcripts** (`len(text) <= 400_000` chars): single API call.

3. **Long transcripts**: chunked summarization:
   - Split transcript at word boundaries into 400K-char chunks
   - Summarize each chunk with the same system prompt
   - Combine chunk summaries, then summarize the combination with a "combine" prompt
   - Token counts are aggregated across all calls

### Constants

| Constant | Value | Notes |
|----------|-------|-------|
| `_MODEL` | `"gpt-4o-mini"` | |
| `_MAX_CHARS_PER_CHUNK` | `400_000` | ~100K tokens at 4 chars/token |
| `_TIMEOUT` | `30` | Seconds per call |

### Internal functions

| Function | Purpose |
|----------|---------|
| `_call_openai(client, system_prompt, user_content)` | Single chat completion call, returns `OpenAIResult` |
| `_split_into_chunks(text, max_chars)` | Splits at word boundaries, returns `list[str]` |
| `_build_length_instruction(word_count, percent)` | Builds the length guidance string |

---

## fallacy_analyzer.py

**File:** [`backend/app/services/fallacy_analyzer.py`](../backend/app/services/fallacy_analyzer.py)
**Model:** `gpt-4o-mini`
**Timeout:** 30s
**Response format:** `json_object` (OpenAI structured output)

### Main function

```python
def analyze_fallacies(transcript_text: str) -> FallacyAnalysisResult | None
```

Returns `None` on any failure (logged as warning, not re-raised).

### Algorithm

1. Send transcript as user message with a detailed system prompt.
2. System prompt instructs the model to:
   - Quote the exact passage for each fallacy
   - Name and categorize the fallacy (6 categories)
   - Rate severity: `high` / `medium` / `low`
   - Explain in 2–3 sentences
   - Provide a clear example in a different context
   - Be conservative — only flag genuinely flawed reasoning
3. Use `response_format={"type": "json_object"}` to guarantee parseable JSON.
4. Parse the JSON into `FallacyAnalysisResult`.

### Fallacy categories

`Relevance` | `Presumption` | `Ambiguity` | `Emotional Appeal` | `Statistical` | `Manipulation`

---

## qa.py

**File:** [`backend/app/services/qa.py`](../backend/app/services/qa.py)
**Model:** `gpt-4o` (full model for conversational quality)
**Timeout:** 30s
**Async:** yes (`AsyncOpenAI`)

### Main function

```python
async def ask_question(
    transcript: str,
    question: str,
    history: list[dict],
) -> str
```

Returns the assistant's answer as a plain string.

### Algorithm

1. Build message list:
   ```
   [system: "...Transcript:\n{transcript}"]
   + history (list of {role, content} dicts)
   + [user: question]
   ```
2. Async call to `gpt-4o`.
3. Return `response.choices[0].message.content`.

The system prompt grounds the assistant in the transcript only: *"Use only the transcript content to answer."* This prevents hallucination about video content.

---

## transcript.py

**File:** [`backend/app/services/transcript.py`](../backend/app/services/transcript.py)

### Functions

```python
def get_transcript(video_id: str) -> tuple[str, list[dict]]
def calculate_duration(segments: list[dict]) -> int | None
```

`get_transcript` returns `(full_text, raw_segments)` where:
- `full_text` — all segment texts joined with spaces
- `raw_segments` — list of `{text, start, duration}` dicts

`calculate_duration` returns `int(last_segment["start"] + last_segment["duration"])` or `None` if empty.

### Cookie authentication

If `/app/cookies.txt` exists, it is loaded as a `MozillaCookieJar` and attached to the requests session passed to `YouTubeTranscriptApi`. This allows the transcript API to authenticate as a browser, bypassing IP-based blocks.

```python
COOKIES_PATH = "/app/cookies.txt"   # mounted via docker-compose volume
```

In Docker: `./cookies.txt:/app/cookies.txt:ro` in `docker-compose.yml`.

### Exceptions raised (handled in `main.py`)

| Exception | HTTP status | Error code |
|-----------|-------------|------------|
| `IpBlocked`, `RequestBlocked` | 503 | `ip_blocked` |
| `VideoUnavailable` | 404 | `video_not_found` |
| `TranscriptsDisabled`, `NoTranscriptFound` | 404 | `transcript_unavailable` |

---

## youtube.py

**File:** [`backend/app/services/youtube.py`](../backend/app/services/youtube.py)

### Functions

```python
def extract_video_id(url: str) -> str
def get_video_metadata(video_id: str) -> VideoMetadata
```

### URL parsing

`extract_video_id` uses a single regex:

```python
r"(?:youtube\.com/(?:watch\?.*v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
```

Supported URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`

Playlist detection: raises `ValueError("Playlist URLs are not supported...")` if the URL has `list=` but no `v=`, or if the path is `/playlist`.

### Metadata fetching

`get_video_metadata` calls YouTube's public oEmbed endpoint:
```
https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json
```

Returns `VideoMetadata(video_id, title, channel_name, thumbnail_url)`.
On HTTP error: returns `VideoMetadata(video_id=video_id)` with all other fields `None`. Metadata failures never block the summary response.
