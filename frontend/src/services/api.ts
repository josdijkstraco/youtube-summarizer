import type { SummarizeResponse, ErrorResponse } from "@/types";

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
