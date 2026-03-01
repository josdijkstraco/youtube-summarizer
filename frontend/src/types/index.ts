export interface SummarizeRequest {
  url: string;
  length_percent?: number;
}

export interface VideoMetadata {
  video_id: string;
  title: string | null;
  channel_name: string | null;
  duration_seconds: number | null;
  thumbnail_url: string | null;
}

export interface ClearExample {
  scenario: string;
  why_wrong: string;
}

export interface Fallacy {
  timestamp: string | null;
  quote: string;
  fallacy_name: string;
  category: string;
  severity: string;
  explanation: string;
  clear_example: ClearExample;
}

export interface FallacySummary {
  total_fallacies: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  primary_tactics: string[];
}

export interface FallacyAnalysisResult {
  summary: FallacySummary;
  fallacies: Fallacy[];
}

export interface Highlight {
  start: number;
  end: number;
}

export interface SummaryStats {
  chars_in: number;
  chars_out: number;
  total_tokens: number;
  generation_seconds: number;
}

export interface SummarizeResponse {
  summary: string;
  transcript: string;
  metadata: VideoMetadata | null;
  storage_warning?: boolean;
  stats: SummaryStats | null;
  highlights?: Highlight[];
}

export interface ErrorResponse {
  error: string;
  message: string;
  details: string | null;
}

export interface HistoryItem {
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  summary: string;
  has_fallacy_analysis: boolean;
  created_at: string; // ISO 8601 timestamp
}

export interface HistoryResponse {
  items: HistoryItem[];
}

export interface VideoRecord {
  id: number;
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  summary: string;
  transcript: string;
  fallacy_analysis: FallacyAnalysisResult | null;
  highlights: Highlight[];
  qa_history: QaMessage[];
  created_at: string;
}

export interface QaMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AskRequest {
  transcript: string;
  question: string;
  history: QaMessage[];
  video_id?: string;
}

export interface AskResponse {
  answer: string;
}
