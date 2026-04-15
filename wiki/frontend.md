# Frontend

**Framework:** Vue 3 (Composition API)  
**Build tool:** Vite 5.4  
**Language:** TypeScript 5.5  
**Entry point:** [`frontend/src/main.ts`](../frontend/src/main.ts)  
**Root component:** [`frontend/src/App.vue`](../frontend/src/App.vue)

---

## Component Tree

```
App.vue  (top-level state container)
├── HistoryPanel.vue  (sidebar drawer)
│   └── HistoryCard.vue  (one card per video)
├── UrlInput.vue  (URL paste + submit)
├── LengthSlider.vue  (10–50% summary length)
├── LoadingState.vue  (spinner during summarization)
├── ErrorMessage.vue  (error toast)
├── SummaryDisplay.vue  (main content tabs)
│   ├── Summary tab  — rendered summary text
│   ├── Transcript tab  — full transcript + highlight overlay
│   ├── Q&A tab  — conversation interface
│   └── Notes tab  — auto-saving text editor
├── FallacySummaryPanel.vue  (severity counts + primary tactics)
└── FallacyDisplay.vue  (fallacy table with expandable rows)
```

---

## App.vue

**File:** [`frontend/src/App.vue`](../frontend/src/App.vue)

### State refs

| Ref | Type | Purpose |
|-----|------|---------|
| `loading` | `boolean` | Summarization in progress |
| `summary` | `string \| null` | Current summary text |
| `transcript` | `string \| null` | Current transcript text |
| `metadata` | `VideoMetadata \| null` | Title, channel, thumbnail, duration |
| `stats` | `SummaryStats \| null` | Token counts, timing |
| `fallacyAnalysis` | `FallacyAnalysisResult \| null` | Fallacy results |
| `error` | `string \| null` | Error message for ErrorMessage.vue |
| `fallacyError` | `string \| null` | Error from fallacy analysis |
| `submittedUrl` | `string` | URL of the currently displayed video |
| `currentVideoId` | `string \| null` | video_id for persistence calls |
| `currentHighlights` | `Highlight[]` | Active highlights (passed to SummaryDisplay) |
| `currentQaHistory` | `QaMessage[]` | Active Q&A history |
| `currentNotes` | `string \| null` | Active notes |
| `drawerOpen` | `boolean` | History sidebar open/closed |

### Key functions

| Function | Triggered by | What it does |
|----------|-------------|--------------|
| `handleSubmit(url)` | UrlInput submit | Calls `summarizeVideo()`, populates all state refs, reloads history |
| `handleAnalyzeFallacies()` | Button click | Calls `analyzeFallacies(submittedUrl)`, sets `fallacyAnalysis` |
| `handleSelectVideo(videoId)` | HistoryCard click | Calls `fetchHistoryItem()`, loads full VideoRecord into all state refs |
| `handleRetry()` | ErrorMessage retry | Clears `error` and `loading` |

### LengthSlider

Slider value (10–50, step 5) is passed as `lengthPercent` to `handleSubmit` → `summarizeVideo(url, lengthPercent)`. Not persisted — session-only.

---

## SummaryDisplay.vue

**File:** [`frontend/src/components/SummaryDisplay.vue`](../frontend/src/components/SummaryDisplay.vue)

### Props

```typescript
props: {
  summary: string
  transcript: string
  metadata: VideoMetadata | null
  stats: SummaryStats | null
  videoId: string | null
  initialHighlights: Highlight[]
  initialQaHistory: QaMessage[]
  initialNotes: string | null
}
```

### Tabs

**Summary tab**
- Renders `summary` with paragraph formatting.

**Transcript tab**
- Renders full `transcript` with highlight overlay.
- Click on text → popover appears → click "Highlight" → calls `api.addHighlight(videoId, start, end)`.
- Double-click a highlighted region → popover appears → click "Remove" → calls `api.removeHighlight(videoId, index)`.
- Highlights auto-merge in the backend; updated list is returned and re-rendered.

**Q&A tab**
- Conversation interface showing `QaMessage[]` in chronological order.
- Input textarea: `Enter` submits, `Shift+Enter` inserts newline.
- On submit: calls `api.askQuestion(transcript, question, history, videoId)`.
- Response appended to message list; list auto-scrolls to bottom.
- Conversation persisted to database via `video_id`.

**Notes tab**
- Free-form `<textarea>`.
- Auto-saves on change with 1-second debounce: calls `api.saveNotes(videoId, notes)`.
- Shows status indicator: `saving...` → `saved` / `error`.
- Cleared (reset to `null`) when a new video is loaded.

---

## HistoryPanel.vue

**File:** [`frontend/src/components/HistoryPanel.vue`](../frontend/src/components/HistoryPanel.vue)

- Fetches `GET /api/history?limit=50` on open and after any mutating operation.
- Renders one `HistoryCard` per `HistoryItem`.
- Emits `select-video(videoId)` → App.vue `handleSelectVideo`.

**Delete flow:**
1. `HistoryCard` delete button → `deleteHistoryItem(videoId)`.
2. Shows 5-second undo toast.
3. If undo clicked → `restoreHistoryItem(videoId)`.
4. History list reloads after either path.

---

## HistoryCard.vue

**File:** [`frontend/src/components/HistoryCard.vue`](../frontend/src/components/HistoryCard.vue)

Displays per-video:
- Thumbnail image
- Title + summary preview (truncated)
- "Fallacy Analysis" badge if `has_fallacy_analysis === true`
- Delete button

---

## FallacyDisplay.vue

**File:** [`frontend/src/components/FallacyDisplay.vue`](../frontend/src/components/FallacyDisplay.vue)

Table with columns: Quote | Fallacy Name | Severity | Category | Explanation.  
Rows are expandable to show `clear_example.scenario` and `clear_example.why_wrong`.  
Severity color coding: high = red, medium = yellow, low = green.

---

## FallacySummaryPanel.vue

**File:** [`frontend/src/components/FallacySummaryPanel.vue`](../frontend/src/components/FallacySummaryPanel.vue)

Displays `FallacySummary`: total count, high/medium/low breakdown, primary tactics list.

---

## API Service

**File:** [`frontend/src/services/api.ts`](../frontend/src/services/api.ts)

Base URL: `import.meta.env.VITE_API_URL || "http://localhost:8000"`

All functions throw `ApiError` (extends `Error`) on non-2xx responses. `ApiError.errorResponse` contains the `ErrorResponse` object from the backend.

| Function | Method | Endpoint | Returns |
|----------|--------|----------|---------|
| `summarizeVideo(url, lengthPercent?)` | POST | `/api/summarize` | `SummarizeResponse` |
| `analyzeFallacies(url)` | POST | `/api/fallacies` | `FallacyAnalysisResult` |
| `fetchHistory(limit?)` | GET | `/api/history` | `HistoryResponse` |
| `fetchHistoryItem(videoId)` | GET | `/api/history/{videoId}` | `VideoRecord` |
| `deleteHistoryItem(videoId)` | DELETE | `/api/history/{videoId}` | `void` |
| `restoreHistoryItem(videoId)` | POST | `/api/history/{videoId}/restore` | `HistoryItem` |
| `addHighlight(videoId, start, end)` | POST | `/api/history/{videoId}/highlights` | `Highlight[]` |
| `removeHighlight(videoId, index)` | DELETE | `/api/history/{videoId}/highlights/{index}` | `Highlight[]` |
| `saveNotes(videoId, notes)` | PUT | `/api/history/{videoId}/notes` | `void` |
| `askQuestion(transcript, question, history, videoId?)` | POST | `/api/ask` | `AskResponse` |

---

## Environment Variables

| Variable | Where set | Default | Purpose |
|----------|-----------|---------|---------|
| `VITE_API_URL` | build arg / `.env` | `http://localhost:8000` | Backend base URL |

In Docker, set via `docker-compose.yml` build arg:
```yaml
args:
  VITE_API_URL: http://localhost:8002
```

---

## Build & Dev Commands

```bash
npm run dev        # Vite dev server with HMR at http://localhost:5173
npm run build      # TypeScript type-check + production build → dist/
npm run lint       # ESLint + Prettier check
npm run lint:fix   # Auto-fix lint issues
npm run test       # Vitest unit tests
```
