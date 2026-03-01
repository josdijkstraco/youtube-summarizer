<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from "vue";
import type { VideoMetadata, SummaryStats, Highlight, QaMessage } from "@/types";
import { addHighlight, removeHighlight, askQuestion } from "@/services/api";

const props = defineProps<{
  summary: string;
  transcript: string;
  metadata?: VideoMetadata | null;
  stats?: SummaryStats | null;
  videoId?: string | null;
  initialHighlights?: Highlight[];
  initialQaHistory?: QaMessage[];
}>();

const activeTab = ref<"summary" | "transcript" | "qa">("summary");
const highlights = ref<Highlight[]>(props.initialHighlights ?? []);
const contentEl = ref<HTMLElement | null>(null);

interface Popover {
  type: "add" | "remove";
  x: number;
  y: number;
  start?: number;
  end?: number;
  index?: number;
}
const popover = ref<Popover | null>(null);

// Q&A state
const qaHistory = ref<QaMessage[]>(props.initialQaHistory ?? []);
const qaInput = ref("");
const qaLoading = ref(false);
const qaError = ref<string | null>(null);
const qaMessagesEl = ref<HTMLElement | null>(null);

async function sendQuestion() {
  const question = qaInput.value.trim();
  if (!question || qaLoading.value) return;

  const priorHistory = [...qaHistory.value];
  qaHistory.value = [...priorHistory, { role: "user", content: question }];
  qaInput.value = "";
  qaLoading.value = true;
  qaError.value = null;

  try {
    const { answer } = await askQuestion(props.transcript, question, priorHistory, props.videoId ?? undefined);
    qaHistory.value = [...qaHistory.value, { role: "assistant", content: answer }];
  } catch (err) {
    qaError.value = err instanceof Error ? err.message : "Failed to get answer.";
  } finally {
    qaLoading.value = false;
  }
}

function onQaKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
}

// Reset highlights when initialHighlights prop changes (e.g. new video loaded)
watch(
  () => props.initialHighlights,
  (val) => {
    highlights.value = val ?? [];
  },
);

// Reset Q&A history when initialQaHistory prop changes (new video loaded)
watch(
  () => props.initialQaHistory,
  (val) => {
    qaHistory.value = val ?? [];
    qaInput.value = "";
    qaError.value = null;
  },
);

// Scroll to bottom when messages change or loading indicator appears
watch(
  [qaHistory, qaLoading],
  async () => {
    await nextTick();
    if (qaMessagesEl.value) {
      qaMessagesEl.value.scrollTop = qaMessagesEl.value.scrollHeight;
    }
  },
);

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function mergeHighlights(hl: Highlight[]): Highlight[] {
  if (!hl.length) return [];
  const sorted = [...hl].sort((a, b) => a.start - b.start);
  const merged: Highlight[] = [{ ...sorted[0] }];
  for (const h of sorted.slice(1)) {
    const last = merged[merged.length - 1];
    if (h.start <= last.end) {
      last.end = Math.max(last.end, h.end);
    } else {
      merged.push({ ...h });
    }
  }
  return merged;
}

// Build HTML for the summary with <mark> tags around highlights.
// Paragraphs are split on \n\n; each boundary adds 2 chars to offsets.
const highlightedSummaryHtml = computed(() => {
  const text = props.summary;
  const merged = mergeHighlights(highlights.value);

  if (!merged.length) {
    const paras = text
      .split("\n\n")
      .map((p) => `<p class="summary-display__paragraph">${escapeHtml(p)}</p>`)
      .join("");
    return paras;
  }

  // Build events map: position → {opens: index[], closes: index[]}
  const openAt = new Map<number, number[]>();
  const closeAt = new Map<number, number[]>();

  merged.forEach((hl, idx) => {
    if (!openAt.has(hl.start)) openAt.set(hl.start, []);
    openAt.get(hl.start)!.push(idx);
    if (!closeAt.has(hl.end)) closeAt.set(hl.end, []);
    closeAt.get(hl.end)!.push(idx);
  });

  let html = "";
  const paragraphs = text.split("\n\n");
  let charOffset = 0;

  paragraphs.forEach((para, paraIdx) => {
    if (paraIdx > 0) {
      charOffset += 2; // account for \n\n separator
    }

    let paraHtml = "";
    for (let i = 0; i < para.length; i++) {
      const pos = charOffset + i;
      const closes = closeAt.get(pos);
      if (closes) {
        for (let k = 0; k < closes.length; k++) {
          paraHtml += "</mark>";
        }
      }
      const opens = openAt.get(pos);
      if (opens) {
        for (let k = 0; k < opens.length; k++) {
          paraHtml += `<mark class="summary-highlight" data-highlight-index="${opens[k]}">`;
        }
      }
      paraHtml += escapeHtml(para[i]);
    }

    // Close marks that end at the paragraph boundary
    const endPos = charOffset + para.length;
    const closesAtEnd = closeAt.get(endPos);
    if (closesAtEnd) {
      for (let k = 0; k < closesAtEnd.length; k++) {
        paraHtml += "</mark>";
      }
    }

    charOffset += para.length;
    html += `<p class="summary-display__paragraph">${paraHtml}</p>`;
  });

  return html;
});

// Convert a DOM selection within contentEl to character offsets in the summary string.
// Each \n\n paragraph separator = 2 chars. DOM has <p> elements per paragraph.
function domSelectionToStringOffsets(
  container: HTMLElement,
  sel: Selection,
): { start: number; end: number } {
  const range = sel.getRangeAt(0);
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);

  let textOffset = 0;
  let paraBreakOffset = 0;
  let prevPara: Element | null = null;
  let start = 0;
  let end = 0;
  let startFound = false;
  let endFound = false;

  let node = walker.nextNode();
  while (node !== null) {
    const textNode = node as Text;

    // Find the nearest <p> ancestor
    let parentPara: Element | null = null;
    let el: Node | null = textNode.parentNode;
    while (el !== null && el !== container) {
      if ((el as Element).tagName === "P") {
        parentPara = el as Element;
        break;
      }
      el = el.parentNode;
    }

    // Crossed a paragraph boundary → add 2 for \n\n
    if (parentPara !== prevPara) {
      if (prevPara !== null) {
        paraBreakOffset += 2;
      }
      prevPara = parentPara;
    }

    const offset = textOffset + paraBreakOffset;

    if (!startFound && textNode === range.startContainer) {
      start = offset + range.startOffset;
      startFound = true;
    }
    if (!endFound && textNode === range.endContainer) {
      end = offset + range.endOffset;
      endFound = true;
    }

    textOffset += textNode.length;

    if (startFound && endFound) break;
    node = walker.nextNode();
  }

  return { start, end };
}

function onSummaryMouseUp(e: MouseEvent) {
  // Mark clicks are handled separately
  if ((e.target as HTMLElement).closest(".summary-highlight")) return;
  if (!props.videoId || activeTab.value !== "summary") return;

  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !contentEl.value) {
    popover.value = null;
    return;
  }

  const { start, end } = domSelectionToStringOffsets(contentEl.value, sel);
  if (start >= end) {
    popover.value = null;
    return;
  }

  const rect = sel.getRangeAt(0).getBoundingClientRect();
  popover.value = {
    type: "add",
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
    start,
    end,
  };
}

function onMarkClick(e: MouseEvent) {
  if (!props.videoId || activeTab.value !== "summary") return;

  const mark = (e.target as HTMLElement).closest(
    "[data-highlight-index]",
  ) as HTMLElement | null;
  if (!mark) return;

  e.stopPropagation();
  const index = parseInt(mark.getAttribute("data-highlight-index")!);
  const rect = mark.getBoundingClientRect();
  popover.value = {
    type: "remove",
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
    index,
  };
}

async function handleSaveHighlight() {
  if (!props.videoId || !popover.value || popover.value.type !== "add") return;
  const { start, end } = popover.value;
  if (start == null || end == null) return;
  highlights.value = await addHighlight(props.videoId, start, end);
  popover.value = null;
  window.getSelection()?.removeAllRanges();
}

async function handleRemoveHighlight() {
  if (
    !props.videoId ||
    !popover.value ||
    popover.value.type !== "remove" ||
    popover.value.index == null
  )
    return;
  highlights.value = await removeHighlight(props.videoId, popover.value.index);
  popover.value = null;
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === "Escape") popover.value = null;
}

function onDocumentClick(e: MouseEvent) {
  // Don't dismiss when user just finished selecting text — the click fires
  // right after mouseup and the selection is still non-collapsed.
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed) return;

  const target = e.target as HTMLElement;
  if (
    !target.closest(".highlight-popover") &&
    !target.closest(".summary-highlight")
  ) {
    popover.value = null;
  }
}

onMounted(() => {
  document.addEventListener("keydown", onKeyDown);
  document.addEventListener("click", onDocumentClick, true);
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeyDown);
  document.removeEventListener("click", onDocumentClick, true);
});
</script>

<template>
  <div class="summary-display">
    <div v-if="metadata" class="summary-display__meta">
      <a
        :href="`https://www.youtube.com/watch?v=${metadata.video_id}`"
        target="_blank"
        rel="noopener noreferrer"
        class="summary-display__thumb-link"
      >
        <img
          v-if="metadata.thumbnail_url"
          :src="metadata.thumbnail_url"
          :alt="metadata.title ?? 'Video thumbnail'"
          class="summary-display__thumbnail"
        />
      </a>
      <div class="summary-display__meta-text">
        <h2 v-if="metadata.title" class="summary-display__title">
          <a
            :href="`https://www.youtube.com/watch?v=${metadata.video_id}`"
            target="_blank"
            rel="noopener noreferrer"
            class="summary-display__title-link"
          >
            {{ metadata.title }}
          </a>
        </h2>
        <div class="summary-display__meta-row">
          <span v-if="metadata.channel_name" class="summary-display__channel">
            {{ metadata.channel_name }}
          </span>
          <span
            v-if="metadata.duration_seconds != null"
            class="summary-display__duration"
          >
            {{ formatDuration(metadata.duration_seconds) }}
          </span>
        </div>
      </div>
    </div>
    <div v-if="stats" class="summary-display__stats">
      <span class="summary-display__stat">
        <span class="summary-display__stat-label">Chars in</span>
        <span class="summary-display__stat-value">{{ stats.chars_in.toLocaleString() }}</span>
      </span>
      <span class="summary-display__stat">
        <span class="summary-display__stat-label">Chars out</span>
        <span class="summary-display__stat-value">{{ stats.chars_out.toLocaleString() }}</span>
      </span>
      <span class="summary-display__stat">
        <span class="summary-display__stat-label">Total tokens</span>
        <span class="summary-display__stat-value">{{ stats.total_tokens.toLocaleString() }}</span>
      </span>
      <span class="summary-display__stat">
        <span class="summary-display__stat-label">Time</span>
        <span class="summary-display__stat-value">{{ stats.generation_seconds }}s</span>
      </span>
    </div>
    <div class="summary-display__tabs">
      <button
        :class="[
          'summary-display__tab',
          { 'is-active': activeTab === 'summary' },
        ]"
        @click="activeTab = 'summary'"
      >
        Summary
      </button>
      <button
        :class="[
          'summary-display__tab',
          { 'is-active': activeTab === 'transcript' },
        ]"
        @click="activeTab = 'transcript'"
      >
        Transcript
      </button>
      <button
        :class="[
          'summary-display__tab',
          { 'is-active': activeTab === 'qa' },
        ]"
        @click="activeTab = 'qa'"
      >
        Q&amp;A
      </button>
    </div>
    <div
      v-if="activeTab !== 'qa'"
      ref="contentEl"
      class="summary-display__content"
      @mouseup="onSummaryMouseUp"
      @click="onMarkClick"
    >
      <template v-if="activeTab === 'summary'">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div v-html="highlightedSummaryHtml" />
      </template>
      <p v-else class="summary-display__transcript">{{ transcript }}</p>
    </div>

    <!-- Q&A panel -->
    <div v-if="activeTab === 'qa'" class="summary-display__qa">
      <div ref="qaMessagesEl" class="summary-display__qa-messages">
        <div
          v-for="(msg, i) in qaHistory"
          :key="i"
          :class="['qa-message', `qa-message--${msg.role}`]"
        >
          <div class="qa-message__bubble">{{ msg.content }}</div>
        </div>
        <div v-if="qaLoading" class="qa-message qa-message--assistant">
          <div class="qa-message__bubble qa-message__bubble--loading">
            <span class="qa-loading-dot" />
            <span class="qa-loading-dot" />
            <span class="qa-loading-dot" />
          </div>
        </div>
        <p v-if="qaError" class="qa-error">{{ qaError }}</p>
      </div>
      <div class="summary-display__qa-input">
        <textarea
          v-model="qaInput"
          class="qa-textarea"
          placeholder="Ask a question about this video…"
          rows="2"
          :disabled="qaLoading"
          @keydown="onQaKeydown"
        />
        <button
          class="qa-send-btn"
          :disabled="!qaInput.trim() || qaLoading"
          @click="sendQuestion"
        >
          Send
        </button>
      </div>
    </div>

    <!-- Highlight popover — teleported to body to avoid clipping -->
    <Teleport to="body">
      <div
        v-if="popover"
        class="highlight-popover"
        :style="{
          left: `${popover.x}px`,
          top: `${popover.y}px`,
        }"
      >
        <template v-if="popover.type === 'add'">
          <button
            class="highlight-popover__btn highlight-popover__btn--add"
            @click.stop="handleSaveHighlight"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" opacity="0.15"/>
              <rect x="3" y="11" width="18" height="2"/>
              <rect x="11" y="3" width="2" height="18"/>
            </svg>
            Save highlight
          </button>
        </template>
        <template v-else>
          <button
            class="highlight-popover__btn highlight-popover__btn--remove"
            @click.stop="handleRemoveHighlight"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6M14 11v6" />
              <path d="M9 6V4h6v2" />
            </svg>
            Remove highlight
          </button>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.summary-display {
  width: 100%;
  max-width: 720px;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 6px 24px rgba(0, 0, 0, 0.02);
}

.summary-display__meta {
  display: flex;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  align-items: center;
}

.summary-display__thumbnail {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
  transition: opacity 0.15s, transform 0.15s;
}

.summary-display__thumb-link {
  flex-shrink: 0;
}

.summary-display__thumb-link:hover .summary-display__thumbnail {
  opacity: 0.85;
  transform: scale(1.03);
}

.summary-display__meta-text {
  flex: 1;
  min-width: 0;
}

.summary-display__title {
  margin: 0 0 0.3rem;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.35;
}

.summary-display__title-link {
  color: inherit;
  text-decoration: none;
}

.summary-display__title-link:hover {
  text-decoration: underline;
}

.summary-display__meta-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.summary-display__channel {
  font-size: 0.8rem;
  color: #6B7280;
}

.summary-display__duration {
  font-size: 0.8rem;
  color: #9CA3AF;
  font-variant-numeric: tabular-nums;
}

.summary-display__stats {
  display: flex;
  gap: 1.25rem;
  padding: 0.6rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
}

.summary-display__stat {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
}

.summary-display__stat-label {
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9CA3AF;
  font-family: 'Manrope', sans-serif;
}

.summary-display__stat-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: #111827;
  font-variant-numeric: tabular-nums;
  font-family: 'Manrope', sans-serif;
}

.summary-display__tabs {
  display: flex;
  gap: 0;
  padding: 0 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.summary-display__tab {
  padding: 0.75rem 0;
  margin-right: 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  color: #9CA3AF;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.summary-display__tab:hover {
  color: #111827;
}

.summary-display__tab.is-active {
  color: #111827;
  border-bottom-color: #2563EB;
}

.summary-display__content {
  padding: 1.5rem;
  line-height: 1.75;
  color: #374151;
  font-size: 0.95rem;
}

.summary-display__transcript {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.75;
  color: #4B5563;
}

/* Q&A panel */
.summary-display__qa {
  display: flex;
  flex-direction: column;
  height: 480px;
}

.summary-display__qa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.summary-display__qa-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem 1.25rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  align-items: flex-end;
}

.qa-textarea {
  flex: 1;
  resize: none;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-family: 'Manrope', sans-serif;
  line-height: 1.5;
  color: #111827;
  outline: none;
  transition: border-color 0.15s;
}

.qa-textarea:focus {
  border-color: #2563EB;
}

.qa-textarea:disabled {
  opacity: 0.6;
}

.qa-send-btn {
  padding: 0.5rem 1rem;
  background: #2563EB;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  white-space: nowrap;
}

.qa-send-btn:hover:not(:disabled) {
  background: #1D4ED8;
}

.qa-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qa-error {
  margin: 0;
  font-size: 0.8rem;
  color: #B91C1C;
}

/* Chat messages */
.qa-message {
  display: flex;
}

.qa-message--user {
  justify-content: flex-end;
}

.qa-message--assistant {
  justify-content: flex-start;
}

.qa-message__bubble {
  max-width: 80%;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.qa-message--user .qa-message__bubble {
  background: #2563EB;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.qa-message--assistant .qa-message__bubble {
  background: #F3F4F6;
  color: #111827;
  border-bottom-left-radius: 4px;
}

/* Loading dots */
.qa-message__bubble--loading {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.5rem 0.75rem;
}

.qa-loading-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9CA3AF;
  animation: qa-dot-bounce 1.2s infinite;
}

.qa-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.qa-loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes qa-dot-bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
}
</style>

<style>
/* Global styles for v-html content and teleported popover */
.summary-display__paragraph {
  margin: 0 0 1rem;
  white-space: pre-wrap;
}

.summary-display__paragraph:last-child {
  margin-bottom: 0;
}

.summary-highlight {
  background: #FEF08A;
  border-radius: 2px;
  padding: 0 1px;
  cursor: pointer;
  transition: background 0.15s;
}

.summary-highlight:hover {
  background: #FDE047;
}

.highlight-popover {
  position: fixed;
  transform: translate(-50%, -100%);
  margin-top: -6px;
  z-index: 9999;
  background: #FFFFFF;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 4px;
  display: flex;
  align-items: center;
  pointer-events: auto;
}

.highlight-popover__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.highlight-popover__btn--add {
  background: #FEF08A;
  color: #713F12;
}

.highlight-popover__btn--add:hover {
  background: #FDE047;
}

.highlight-popover__btn--remove {
  background: #FEE8E8;
  color: #8B2020;
}

.highlight-popover__btn--remove:hover {
  background: #FFC9C9;
}
</style>
