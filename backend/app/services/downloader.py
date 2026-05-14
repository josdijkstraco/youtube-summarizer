import logging
from pathlib import Path

import yt_dlp  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

_FORMAT = "best[ext=mp4]/best"
_MAX_DURATION_SECONDS = 10800  # 3 hours — prevents accidental huge downloads


def download_video(video_id: str, url: str, output_dir: Path) -> Path:
    output_path = output_dir / f"{video_id}.mp4"

    if output_path.exists():
        logger.info("download_video: %s already exists, skipping yt-dlp", output_path)
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": _FORMAT,
        "outtmpl": str(output_dir / f"{video_id}.%(ext)s"),
        "quiet": True,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = int(info.get("duration") or 0) if info else 0
        if duration > _MAX_DURATION_SECONDS:
            limit_h = _MAX_DURATION_SECONDS // 3600
            raise ValueError(
                f"Video is {duration // 60} min — exceeds the {limit_h}h download limit"
            )
        ydl.download([url])

    if not output_path.exists():
        raise FileNotFoundError(
            f"yt-dlp finished but expected output not found: {output_path}"
        )

    return output_path
