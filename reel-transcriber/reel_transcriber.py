"""CLI: download Instagram Reel audio, transcribe locally, save to a corpus folder."""
import argparse
import csv
import random
import shutil
import sys
import time
from importlib.metadata import version
from pathlib import Path

import download
import export


def read_urls(path: Path) -> list[str]:
    """One URL per line (.txt) or first column (.csv); blanks/headers/duplicates ignored."""
    urls: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row:
                continue
            cell = row[0].strip()
            if cell.startswith("http") and cell not in urls:
                urls.append(cell)
    return urls


def process(url: str, out_dir: Path, transcriber, args) -> bool:
    """Process one URL. Returns True if a download was attempted (for delay purposes)."""
    reel_id = download.extract_reel_id(url)
    if reel_id and not args.force and reel_id in export.completed_ids(out_dir):
        print(f"SKIP  {url} (already in index)")
        return False

    tmp = out_dir / f"_tmp_{reel_id or 'unknown'}"
    meta = {}
    try:
        print(f"GET   {url}")
        dl = download.download_reel(url, tmp)
        meta = dl.metadata
        print(f"      transcribing ({transcriber.model_size}, {transcriber.device})...")
        result = transcriber.transcribe(dl.audio_path, args.language)
        versions = {n: version(n) for n in ("faster-whisper", "ctranslate2", "yt-dlp")}
        folder, words = export.write_reel(out_dir, meta, result, versions)
        if args.keep_audio:
            shutil.move(str(dl.audio_path), folder / dl.audio_path.name)
        export.upsert_index_row(out_dir, {
            "url": url, "reel_id": meta["reel_id"], "username": meta["username"],
            "date": meta["upload_date"], "language": result.language,
            "word_count": words, "folder": str(folder), "status": "ok",
        })
        print(f"OK    {folder.name} [{result.language} {result.language_probability:.2f}, {words} words]")
    except Exception as e:  # one bad URL must not stop the batch
        print(f"FAIL  {url}: {e}")
        export.log_error(out_dir, url, e)
        export.upsert_index_row(out_dir, {
            "url": url, "reel_id": meta.get("reel_id") or reel_id or url,
            "username": meta.get("username", ""), "date": meta.get("upload_date", ""),
            "folder": "", "status": "failed",
        })
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return True


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Transcribe public Instagram Reels locally.")
    p.add_argument("url", nargs="?", help="a single Reel URL")
    p.add_argument("--batch", type=Path, help=".txt/.csv file with one URL per line")
    p.add_argument("--output-dir", type=Path, default=Path("corpus"))
    p.add_argument("--model", default="small", help="Whisper size: tiny/base/small/medium/large-v3")
    p.add_argument("--language", choices=["pt", "it"], help="force language (default: auto-detect)")
    p.add_argument("--keep-audio", action="store_true")
    p.add_argument("--force", action="store_true", help="re-process reels already in the index")
    p.add_argument("--delay-min", type=float, default=5)
    p.add_argument("--delay-max", type=float, default=10)
    args = p.parse_args()

    if bool(args.url) == bool(args.batch):
        p.error("give either a URL or --batch FILE")
    urls = read_urls(args.batch) if args.batch else [args.url]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    from transcribe import Transcriber  # imported late: heavy
    transcriber = Transcriber(args.model)

    for i, url in enumerate(urls):
        downloaded = process(url, args.output_dir, transcriber, args)
        if downloaded and i < len(urls) - 1:
            wait = random.uniform(args.delay_min, args.delay_max)
            print(f"      waiting {wait:.1f}s")
            time.sleep(wait)
    return 0


if __name__ == "__main__":
    sys.exit(main())
