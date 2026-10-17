# Reel Transcriber

Downloads the audio of public Instagram Reels, transcribes it **locally** with faster-whisper, and saves
text + metadata into a traceable corpus. No audio, transcript or metadata leaves your machine. The only
network access is yt-dlp fetching the reel and the one-time download of the Whisper model weights.

## Intended use

This tool is for **academic research purposes only** and must be used **only to analyse publicly available
material**. Users are responsible for complying with Instagram's terms of use, applicable data-protection
rules (e.g. GDPR) and their institution's research-ethics requirements.

## Windows setup

1. Python 3.11+ and ffmpeg. If ffmpeg is missing: `winget install Gyan.FFmpeg` (or `choco install ffmpeg`),
   then open a new terminal and check `ffmpeg -version`.
2. In the project folder:
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Git Bash: source .venv/Scripts/activate
   pip install -r requirements.txt
   ```
   The two `nvidia-*` packages are only needed for an NVIDIA GPU; without a GPU the tool uses CPU (int8).

## Usage

```
Copy the following:
.venv/Scripts/python.exe reel_transcriber.py "https://www.instagram.com/reel/XXXXXXXXXXX/"

.venv/Scripts/python.exe reel_transcriber.py --batch urls.txt     # .txt or .csv, one URL per line (first column)
```

| Flag | Meaning |
|---|---|
| `--model small` | Whisper size (`small` default; `medium` is more accurate, slower) |
| `--language pt\|it` | Force the language instead of auto-detecting |
| `--keep-audio` | Keep the audio file in the reel folder (deleted by default) |
| `--force` | Re-process reels already marked `ok` in the index |
| `--delay-min/--delay-max` | Random pause between downloads in seconds (default 5–10) |
| `--output-dir corpus` | Where everything is written |

## Output

```
corpus/
  corpus_index.csv        URL, ID, username, date, language, word count, folder, status (utf-8-sig)
  errors.log              timestamp, URL, error (failed URLs)
  2025-03-14_username_REELID/
    transcript.txt              plain text, one segment per line
    transcript_timestamped.txt  [mm:ss] per segment
    metadata.json               reel metadata + transcription details
```

Re-runs skip reels with status `ok`; reels with status `failed` are retried.

## Methodological notes (for documenting your method)

- **Model**: faster-whisper (CTranslate2 port of OpenAI Whisper), default `small`. Model, device, compute type and
  library versions are recorded in every `metadata.json`. GPU runs use float16; CPU runs use int8 (int8 can
  differ marginally from float16 output, so keep the same setup across a corpus if exact reproducibility matters).
- **Settings**: faster-whisper defaults (beam size 5, no VAD filter, no initial prompt). Nothing is filtered or
  post-edited; segment text is Whisper's output, whitespace-trimmed. Whisper can hallucinate on music/silence, so
  spot-check reels with background music.
- **Language**: auto-detected by Whisper from the first 30 s of audio; detected language and its probability are
  stored. With `--language`, detection is skipped and `language_forced_by_user` is `true` (the stored
  confidence is then not a measurement of the audio). In code-switching reels, one language is applied to the whole file.
- **Caption**: stored verbatim in `metadata.json` (`caption`) only; it is never mixed into the transcript files.
- **Dates**: `upload_date` is the date Instagram reports (YYYY-MM-DD); `processing_date` is when you ran the tool.
- **Counts**: view and like counts are a snapshot at download time and may be `null` if Instagram hides them.
- **Word count**: whitespace-separated tokens in `transcript.txt`.

## Licence

Released under the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE)
licence. You are free to download, use, share and modify the code, provided you give appropriate credit
(see "How to cite") and do **not** use it for commercial purposes. Third-party components (yt-dlp,
faster-whisper, Whisper model weights) keep their own licences.

## How to cite

Dalla Costa Montanari, S. (2026) Reel-Transcriber. GitHub repository.
