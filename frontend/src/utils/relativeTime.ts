/**
 * Format an ISO timestamp as a human-readable relative time (e.g. "3 hours ago").
 *
 * Pure function with no side effects. The optional `now` argument exists for
 * deterministic tests; when omitted it defaults to the current time.
 *
 * @param iso - An ISO 8601 timestamp string.
 * @param now - Optional reference time (defaults to `new Date()`).
 * @returns A relative-time phrase such as "just now" or "2 days ago".
 */
export function formatRelativeTime(iso: string, now?: Date): string {
  let ms = (now ?? new Date()).getTime() - new Date(iso).getTime();
  if (ms < 0) ms = 0;
  const s = Math.floor(ms / 1000);
  if (s < 60) return "just now";
  if (s < 3600) {
    const n = Math.floor(s / 60);
    return `${n} minute${n === 1 ? "" : "s"} ago`;
  }
  if (s < 86400) {
    const n = Math.floor(s / 3600);
    return `${n} hour${n === 1 ? "" : "s"} ago`;
  }
  if (s < 604800) {
    const n = Math.floor(s / 86400);
    return `${n} day${n === 1 ? "" : "s"} ago`;
  }
  if (s < 2592000) {
    const n = Math.floor(s / 604800);
    return `${n} week${n === 1 ? "" : "s"} ago`;
  }
  if (s < 31536000) {
    const n = Math.floor(s / 2592000);
    return `${n} month${n === 1 ? "" : "s"} ago`;
  }
  const n = Math.floor(s / 31536000);
  return `${n} year${n === 1 ? "" : "s"} ago`;
}
