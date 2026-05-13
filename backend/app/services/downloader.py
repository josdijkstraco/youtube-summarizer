import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

_in_docker = Path("/.dockerenv").exists()
_project_root = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data" if _in_docker else str(_project_root / "data")))
COOKIES_PATH = Path(os.environ.get("COOKIES_PATH", "/app/cookies.txt" if _in_docker else str(_project_root / "cookies.txt")))
FORMAT = "best[height<=720][ext=mp4]/best[height<=720]/best"

_downloading: set[str] = set()
_errors: dict[str, str] = {}


def get_download_status(video_id: str) -> Literal["not_downloaded", "downloading", "ready", "error"]:
    if video_id in _downloading:
        return "downloading"
    if (DATA_DIR / f"{video_id}.mp4").exists():
        return "ready"
    if video_id in _errors:
        return "error"
    return "not_downloaded"


def get_download_error(video_id: str) -> str | None:
    return _errors.get(video_id)


async def start_download(video_id: str) -> None:
    if get_download_status(video_id) in ("downloading", "ready"):
        return
    _errors.pop(video_id, None)
    _downloading.add(video_id)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        "yt-dlp",
        "-f", FORMAT,
        "-o", str(DATA_DIR / f"{video_id}.mp4"),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    tmp_cookies: Path | None = None
    if COOKIES_PATH.exists():
        fd, tmp_path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        tmp_cookies = Path(tmp_path)
        shutil.copy2(COOKIES_PATH, tmp_cookies)
        args += ["--cookies", str(tmp_cookies)]
    try:
        await asyncio.to_thread(subprocess.run, args, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace").strip() if e.stderr else ""
        _errors[video_id] = stderr or f"yt-dlp exited with status {e.returncode}"
    except Exception as e:
        _errors[video_id] = str(e)
    finally:
        _downloading.discard(video_id)
        if tmp_cookies:
            tmp_cookies.unlink(missing_ok=True)


def delete_video_file(video_id: str) -> None:
    path = DATA_DIR / f"{video_id}.mp4"
    path.unlink(missing_ok=True)
