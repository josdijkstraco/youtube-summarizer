# Data Models

Pydantic models live in [`backend/app/models.py`](../backend/app/models.py).  
TypeScript interfaces live in [`frontend/src/types/index.ts`](../frontend/src/types/index.ts).

---

## Request Models

### `SummarizeRequest`

```python
class SummarizeRequest(BaseModel):
    url: str               # trimmed, must not be empty
    length_percent: int    # 10–50, multiple of 5. Default: 25
```

```typescript
interface SummarizeRequest {
  url: string;
  length_percent?: number;
}
```

### `FallacyAnalysisRequest`

```python
class FallacyAnalysisRequest(BaseModel):
    url: str               # trimmed, must not be empty
```

### `AskRequest`

```python
class AskRequest(BaseModel):
    transcript: str
    question: str
    history: list[QaMessage] = []
    video_id: str | None = None
```

```typescript
interface AskRequest {
  transcript: string;
  question: string;
  history: QaMessage[];
  video_id?: string;
}
```

### `HighlightRequest`

```python
class HighlightRequest(BaseModel):
    start: int             # >= 0
    end: int               # >= 0, must be > start
```

### `NotesUpdateRequest`

```python
class NotesUpdateRequest(BaseModel):
    notes: str | None = None
```

---

## Response Models

### `SummarizeResponse`

```python
class SummarizeResponse(BaseModel):
    summary: str
    transcript: str
    metadata: VideoMetadata | None = None
    storage_warning: bool = False
    stats: SummaryStats | None = None
    highlights: list[Highlight] = []
    notes: str | None = None
```

```typescript
interface SummarizeResponse {
  summary: string;
  transcript: string;
  metadata: VideoMetadata | null;
  storage_warning?: boolean;
  stats: SummaryStats | null;
  highlights?: Highlight[];
  notes?: string | null;
}
```

`stats` is `null` for cached (already-stored) responses. `highlights` and `notes` are populated from the database for cached responses.

### `FallacyAnalysisResult`

```python
class FallacyAnalysisResult(BaseModel):
    summary: FallacySummary
    fallacies: list[Fallacy]
```

```typescript
interface FallacyAnalysisResult {
  summary: FallacySummary;
  fallacies: Fallacy[];
}
```

### `AskResponse`

```python
class AskResponse(BaseModel):
    answer: str
```

```typescript
interface AskResponse {
  answer: string;
}
```

### `HistoryResponse`

```python
class HistoryResponse(BaseModel):
    items: list[HistoryItem]
```

```typescript
interface HistoryResponse {
  items: HistoryItem[];
}
```

### `ErrorResponse`

```python
class ErrorResponse(BaseModel):
    error: str       # machine-readable code, e.g. "invalid_url"
    message: str     # human-readable description
    details: str | None = None
```

```typescript
interface ErrorResponse {
  error: string;
  message: string;
  details: string | null;
}
```

---

## Data Types

### `VideoMetadata`

```python
class VideoMetadata(BaseModel):
    video_id: str
    title: str | None = None
    channel_name: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
```

```typescript
interface VideoMetadata {
  video_id: string;
  title: string | null;
  channel_name: string | null;
  duration_seconds: number | null;
  thumbnail_url: string | null;
}
```

### `SummaryStats`

```python
class SummaryStats(BaseModel):
    chars_in: int              # transcript character count
    chars_out: int             # summary character count
    total_tokens: int          # sum of prompt + completion tokens
    generation_seconds: float  # wall-clock time for OpenAI call(s)
```

```typescript
interface SummaryStats {
  chars_in: number;
  chars_out: number;
  total_tokens: number;
  generation_seconds: number;
}
```

### `Highlight`

```python
class Highlight(BaseModel):
    start: int   # character offset in transcript string
    end: int
```

```typescript
interface Highlight {
  start: number;
  end: number;
}
```

### `QaMessage`

```python
class QaMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
```

```typescript
interface QaMessage {
  role: "user" | "assistant";
  content: string;
}
```

### `Fallacy`

```python
class Fallacy(BaseModel):
    timestamp: str | None = None   # e.g. "2:34", from transcript
    quote: str
    fallacy_name: str
    category: str
    severity: str                  # "high" | "medium" | "low"
    explanation: str
    clear_example: ClearExample
```

```typescript
interface Fallacy {
  timestamp: string | null;
  quote: string;
  fallacy_name: string;
  category: string;
  severity: string;
  explanation: string;
  clear_example: ClearExample;
}
```

### `ClearExample`

```python
class ClearExample(BaseModel):
    scenario: str     # a simpler real-world example of the same fallacy
    why_wrong: str    # brief explanation of why it's flawed
```

```typescript
interface ClearExample {
  scenario: string;
  why_wrong: string;
}
```

### `FallacySummary`

```python
class FallacySummary(BaseModel):
    total_fallacies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    primary_tactics: list[str]   # most common fallacy names
```

```typescript
interface FallacySummary {
  total_fallacies: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  primary_tactics: string[];
}
```

### `HistoryItem`

Lightweight record for the history sidebar (no transcript, no JSONB fields).

```python
class HistoryItem(BaseModel):
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    has_fallacy_analysis: bool = False
    created_at: datetime
```

```typescript
interface HistoryItem {
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  summary: string;
  has_fallacy_analysis: boolean;
  created_at: string;  // ISO 8601
}
```

### `VideoRecord`

Full database record returned by `GET /api/history/{video_id}`.

```python
class VideoRecord(BaseModel):
    id: int
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    transcript: str
    fallacy_analysis: FallacyAnalysisResult | None = None
    highlights: list[Highlight] = []
    qa_history: list[QaMessage] = []
    notes: str | None = None
    created_at: datetime
```

```typescript
interface VideoRecord {
  id: number;
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  summary: string;
  transcript: string;
  fallacy_analysis: FallacyAnalysisResult | null;
  highlights: Highlight[];
  qa_history: QaMessage[];
  notes?: string | null;
  created_at: string;
}
```

---

## Backend ↔ Frontend Mapping

| Backend (Pydantic) | Frontend (TypeScript) | Notes |
|--------------------|-----------------------|-------|
| `SummarizeRequest` | `SummarizeRequest` | Identical fields |
| `SummarizeResponse` | `SummarizeResponse` | `storage_warning`, `highlights`, `notes` optional in TS |
| `FallacyAnalysisRequest` | — | Only URL string passed from frontend |
| `FallacyAnalysisResult` | `FallacyAnalysisResult` | Identical |
| `AskRequest` | `AskRequest` | Identical |
| `AskResponse` | `AskResponse` | Identical |
| `VideoMetadata` | `VideoMetadata` | Identical |
| `VideoRecord` | `VideoRecord` | `notes` optional in TS |
| `HistoryItem` | `HistoryItem` | `created_at` is `datetime` in Python, `string` in TS |
| `HistoryResponse` | `HistoryResponse` | Identical |
| `Highlight` | `Highlight` | Identical |
| `QaMessage` | `QaMessage` | Identical |
| `Fallacy` | `Fallacy` | Identical |
| `FallacySummary` | `FallacySummary` | Identical |
| `ClearExample` | `ClearExample` | Identical |
| `SummaryStats` | `SummaryStats` | Identical |
| `ErrorResponse` | `ErrorResponse` | Identical |
