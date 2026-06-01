import { describe, it, expect } from "vitest";
import { formatRelativeTime } from "@/utils/relativeTime";

describe("formatRelativeTime", () => {
  const now = new Date("2026-06-01T00:00:00Z");

  const isoSecondsAgo = (seconds: number): string =>
    new Date(now.getTime() - seconds * 1000).toISOString();

  it.each([
    [30, "just now"],
    [60, "1 minute ago"],
    [120, "2 minutes ago"],
    [3600, "1 hour ago"],
    [7200, "2 hours ago"],
    [86400, "1 day ago"],
    [172800, "2 days ago"],
    [604800, "1 week ago"],
    [1209600, "2 weeks ago"],
    [2592000, "1 month ago"],
    [5184000, "2 months ago"],
    [31536000, "1 year ago"],
    [63072000, "2 years ago"],
  ])("formats %d seconds ago as %j", (seconds, expected) => {
    expect(formatRelativeTime(isoSecondsAgo(seconds), now)).toBe(expected);
  });
});
