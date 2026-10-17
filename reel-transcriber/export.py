"""Write per-reel output files, the master CSV index and the error log."""
import csv
import json
from datetime import datetime
from pathlib import Path

from transcribe import TranscriptionResult, format_timestamp

INDEX_NAME = "corpus_index.csv"
ERRORS_NAME = "errors.log"
FIELDS = ["url", "reel_id", "username", "date", "language", "word_count", "folder", "status"]


def folder_name(meta: dict) -> str:
    return f"{meta['upload_date']}_{meta['username']}_{meta['reel_id']}"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_reel(out_dir: Path, meta: dict, result: TranscriptionResult, versions: dict) -> tuple[Path, int]:
    """Write the three files for a reel. Returns (folder, word_count)."""
    folder = out_dir / folder_name(meta)
    folder.mkdir(parents=True, exist_ok=True)

    plain = "\n".join(s.text for s in result.segments) + "\n"
    stamped = "\n".join(f"{format_timestamp(s.start)} {s.text}" for s in result.segments) + "\n"
    (folder / "transcript.txt").write_text(plain, encoding="utf-8")
    (folder / "transcript_timestamped.txt").write_text(stamped, encoding="utf-8")

    word_count = len(plain.split())
    full_meta = {
        **meta,
        # Instagram often omits duration; fall back to the decoded audio length.
        "duration_seconds": meta.get("duration_seconds") or result.duration_seconds,
        "transcription": {
            "model": result.model,
            "device": result.device,
            "compute_type": result.compute_type,
            "detected_language": result.language,
            "language_confidence": result.language_probability,
            "language_forced_by_user": result.language_forced,
            "word_count": word_count,
            "software_versions": versions,
        },
        "processing_date": now_iso(),
    }
    (folder / "metadata.json").write_text(
        json.dumps(full_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return folder, word_count


def read_index(out_dir: Path) -> list[dict]:
    path = out_dir / INDEX_NAME
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def completed_ids(out_dir: Path) -> set[str]:
    return {r["reel_id"] for r in read_index(out_dir) if r.get("status") == "ok"}


def upsert_index_row(out_dir: Path, row: dict) -> None:
    """Add a row, replacing any earlier row for the same reel ID."""
    rows = [r for r in read_index(out_dir) if r["reel_id"] != row["reel_id"]]
    rows.append({k: row.get(k, "") for k in FIELDS})
    with (out_dir / INDEX_NAME).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def log_error(out_dir: Path, url: str, error: Exception) -> None:
    with (out_dir / ERRORS_NAME).open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()}\t{url}\t{type(error).__name__}: {error}\n")
