export interface SummarizeRequest {
  url: string;
}

export interface VideoMetadata {
  video_id: string;
  title: string | null;
  channel_name: string | null;
  duration_seconds: number | null;
  thumbnail_url: string | null;
}

export interface SummarizeResponse {
  summary: string;
  metadata: VideoMetadata | null;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details: string | null;
}
