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

export interface SummarizeResponse {
  summary: string;
  transcript: string;
  metadata: VideoMetadata | null;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details: string | null;
}
