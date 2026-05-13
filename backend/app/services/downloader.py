from pathlib import Path

import yt_dlp  # type: ignore[import-untyped]


def download_video(video_id: str, url: str, output_dir: Path) -> Path:
    """Download a YouTube video without requiring ffmpeg.

    Uses single-file (pre-merged) formats only. Returns the actual output path,
    which may be .mp4 or another extension depending on what YouTube provides.
    Idempotent: if any file for this video_id already exists, returns it.
    Raises on yt-dlp failure.
    """
    for existing in output_dir.glob(f"{video_id}.*"):
        if existing.suffix not in (".part", ".ytdl", ".tmp"):
            return existing

    ydl_opts = {
        # Prefer pre-merged MP4 progressive stream; fall back to any single-file format.
        # The + operator (separate video+audio merge) is intentionally omitted
        # because merging requires ffmpeg.
        "format": "best[ext=mp4]/best",
        "outtmpl": str(output_dir / f"{video_id}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    ext = (info.get("ext") if info else None) or "mp4"
    output_path = output_dir / f"{video_id}.{ext}"
    if not output_path.exists():
        raise FileNotFoundError(f"Expected download file not found: {output_path}")
    return output_path
