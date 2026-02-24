import type {
  SummarizeResponse,
  FallacyAnalysisResult,
  ErrorResponse,
  HistoryResponse,
  HistoryItem,
  VideoRecord,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  public readonly errorResponse: ErrorResponse;

  constructor(errorResponse: ErrorResponse) {
    super(errorResponse.message);
    this.name = "ApiError";
    this.errorResponse = errorResponse;
  }
}

export async function summarizeVideo(
  url: string,
  lengthPercent?: number,
): Promise<SummarizeResponse> {
  const body: Record<string, unknown> = { url };
  if (lengthPercent !== undefined) {
    body.length_percent = lengthPercent;
  }

  const response = await fetch(`${API_BASE}/api/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "An unexpected error occurred. Please try again.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}

export async function analyzeFallacies(
  url: string,
): Promise<FallacyAnalysisResult> {
  const response = await fetch(`${API_BASE}/api/fallacies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "An unexpected error occurred. Please try again.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}

export async function fetchHistory(limit = 50): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE}/api/history?limit=${limit}`);

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to load history.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}

export async function fetchHistoryItem(videoId: string): Promise<VideoRecord> {
  const response = await fetch(`${API_BASE}/api/history/${videoId}`);

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to load video record.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}

export async function deleteHistoryItem(videoId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/history/${videoId}`, {
    method: "DELETE",
  });

  if (!response.ok && response.status !== 204) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to delete video.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }
}

export async function restoreHistoryItem(
  videoId: string,
): Promise<HistoryItem> {
  const response = await fetch(`${API_BASE}/api/history/${videoId}/restore`, {
    method: "POST",
  });

  if (!response.ok) {
    let errorResponse: ErrorResponse;
    try {
      errorResponse = await response.json();
    } catch {
      errorResponse = {
        error: "internal_error",
        message: "Failed to restore video.",
        details: null,
      };
    }
    throw new ApiError(errorResponse);
  }

  return response.json();
}
