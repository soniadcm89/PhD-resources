"""Download the audio and metadata of a public Instagram Reel with yt-dlp."""
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

_SHORTCODE_RE = re.compile(r"instagram\.com/(?:[\w.]+/)?(?:reels?|p|tv)/([A-Za-z0-9_-]+)")


def extract_reel_id(url: str) -> str | None:
    """Reel ID (shortcode) from the URL, without any network access."""
    m = _SHORTCODE_RE.search(url)
    return m.group(1) if m else None


@dataclass
class ReelDownload:
    audio_path: Path
    metadata: dict


def _clean(name: str) -> str:
    return re.sub(r"[^\w.\-]", "_", name or "unknown", flags=re.UNICODE).strip("_") or "unknown"


def _format_date(info: dict) -> str:
    d = info.get("upload_date")  # YYYYMMDD
    if d and len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return "unknown-date"


def download_reel(url: str, work_dir: Path) -> ReelDownload:
    """Download audio into work_dir and return its path plus normalised metadata.

    Raises on any failure (unavailable, private, rate-limited...).
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(work_dir / "audio.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # Instagram rejects yt-dlp's default TLS fingerprint; present as Chrome (needs curl-cffi).
        "impersonate": ImpersonateTarget("chrome"),
    }
    if shutil.which("ffmpeg"):
        # Strip any video stream so only audio is kept on disk.
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": "0"}
        ]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    files = [p for p in work_dir.glob("audio.*") if p.is_file()]
    if not files:
        raise RuntimeError("yt-dlp finished but no audio file was produced")

    username = info.get("channel") or info.get("uploader_id") or info.get("uploader")
    metadata = {
        "reel_id": info.get("id") or extract_reel_id(url),
        "original_url": url,
        "username": _clean(username),
        "uploader_display_name": info.get("uploader"),
        "upload_date": _format_date(info),
        "caption": info.get("description"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "duration_seconds": info.get("duration"),
    }
    return ReelDownload(audio_path=files[0], metadata=metadata)
