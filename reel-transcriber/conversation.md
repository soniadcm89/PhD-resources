# Conversation: building the Reel Transcriber

Date: 2026-10-17. Tool and tool-output details are condensed; user messages and assistant replies are kept in order.

---

## User: initial brief

Build a small Python tool that takes Instagram Reel URLs, downloads the audio, transcribes it and saves the text, as a research corpus for a PhD (discourse analysis of Portuguese and Italian media).

- **Environment:** Windows, Git Bash, Python 3.11+. Check what is installed first. If ffmpeg is missing, explain how to install it (winget/choco).
- **Data control:** everything local. No audio, transcripts or metadata sent to external services. Network allowed only for yt-dlp and the one-time Whisper model download.
- **Function:**
  1. Input: one URL, or a .txt/.csv with one URL per line (batch). Public reels, no login or cookies.
  2. Download audio only plus metadata with yt-dlp.
  3. Transcribe with faster-whisper: configurable model size (default small), automatic GPU/CPU-int8, language auto-detect with a `pt`/`it` override, segment timestamps.
  4. Output per reel in `{date}_{username}_{reelID}/`: `transcript.txt`, `transcript_timestamped.txt` ([mm:ss]), `metadata.json`; plus a master `corpus_index.csv`.
  5. Delete audio by default, `--keep-audio` to keep.
- **Reliability:** skip already-indexed reels unless `--force`; a failed URL must not stop a batch (log to `errors.log`, mark failed); randomised 5-10 s delay; UTF-8 everywhere (utf-8-sig CSV).
- **Structure:** CLI first, modular (download.py, transcribe.py, export.py), requirements.txt, short README with Windows steps. Test on a public reel before saying it is done.
- **How to work:** short plan first, ask about unclear points, no extra features, explain data-affecting choices for the methodology.

## Assistant: environment check

Checked the machine: Python 3.13, ffmpeg installed via winget, NVIDIA RTX 4070 GPU present. yt-dlp and faster-whisper not installed; project folder empty.

## User

"Go with your recommended defaults for all the open questions and start building."

## Assistant: defaults chosen

- Model `small`, `--model medium` available; faster-whisper defaults (beam 5, no VAD filter, no prompt).
- Language auto-detected by Whisper from the first 30 s; detected language and probability stored; `--language pt|it` forces it.
- Caption stored verbatim in `metadata.json` only, never in the transcript.
- Folder date is the upload date as YYYY-MM-DD.
- Re-runs skip only rows with status `ok`; failed rows are retried.
- Local `.venv`, CUDA libraries via pip, fallback to CPU/int8.

(The assistant acknowledged that its earlier message had shown only a recap, not the plan and questions.)

Built: `download.py`, `transcribe.py`, `export.py`, `reel_transcriber.py`, `requirements.txt`, `README.md`. Verified the CLI runs and Whisper `small` loads on the GPU (`cuda`, `float16`). No real reel tested yet; asked the user for a test URL.

## User

"First, how do I run it?"

## Assistant

```bash
.venv/Scripts/python.exe reel_transcriber.py "https://www.instagram.com/reel/XXXXXXXXXXX/"
.venv/Scripts/python.exe reel_transcriber.py --batch urls.txt
```

Options: `--model medium`, `--language pt|it`, `--keep-audio`, `--force`. Output goes to `corpus/`. Warned that Instagram may refuse anonymous access.

## User

"Doesn't seem to work. Here's a link you can use to test it: https://www.instagram.com/p/Da0Z4Vau3AE/"

## Assistant: diagnosis

Ran the test: Instagram returned "empty media response" even with the latest yt-dlp (2026.08.19) and the `/reel/` URL form. The failure was logged in `errors.log` and the row marked `failed`. Offered two options: check the post in a private window, or add an optional `--cookies` flag (with the warning that it breaks the no-login rule and risks the account).

## User

The post opens in a private window without logging in (a login pop-up appears but can be closed).

## Assistant: fix

- Probed the page directly: Instagram's server returns a skeleton without media data to plain clients.
- Tried yt-dlp with Chrome TLS impersonation (`curl-cffi`): worked. Added `impersonate` to `download.py` and `yt-dlp[curl-cffi]` to `requirements.txt`.
- The next run failed in transcription (`open() got an unexpected keyword argument 'metadata_errors'`), caused by `av` 19 being incompatible with faster-whisper 1.2.1 (the GPU fallback had masked this). Pinned `av>=14,<17`.
- Instagram returned no duration, so `duration_seconds` now falls back to the decoded audio length.

### Test result

Folder `corpus/2026-07-15_mulheresconservadoraspt_Da0Z4Vau3AE/`: `transcript.txt`, `transcript_timestamped.txt`, `metadata.json`, plus a row in `corpus_index.csv` with status `ok`.

- Language `pt`, confidence 0.979, 183 words, model `small` on `cuda`/`float16`, duration 58.96 s.
- `view_count` null (not returned by Instagram), `like_count` 3.
- Re-running printed `SKIP`; `--force` re-processed.

Not tested: a batch with a bad URL, `--model medium`, CPU-only mode.

## User

"Add 3 things in the README: 1) the tool is for research purposes and only to analyse publicly available material. 2) Add the appropriate licence (I don't know if MIT is better, that forbids commercial use). 3) How to cite: Dalla Costa Montanari, S. (2026) Reel-Transcriber. GitHub repository."

## Assistant

- Added an "Intended use" section (research only, public material, user responsible for Instagram terms, GDPR and ethics requirements).
- Pointed out that MIT does **not** forbid commercial use; used PolyForm Noncommercial 1.0.0 with a `LICENSE` file.
- Added the "How to cite" line.

## User

"No, use a more conventional licence. I want people to download this code, use it, edit it, just not for commercial use."

## Assistant

Switched to **CC BY-NC 4.0**: `LICENSE` now holds the full official text with a copyright header; the README licence section says people may download, use, share and modify the code with credit and without commercial use. Noted that Creative Commons itself advises against CC licences for software.

## User

"Perfect, now export this conversation in a MD file."

## Assistant

This file.

---

## Final project files

```
tool/
  reel_transcriber.py   CLI
  download.py           yt-dlp download + metadata
  transcribe.py         faster-whisper (GPU/CPU)
  export.py             output files, CSV index, error log
  requirements.txt
  README.md
  LICENSE               CC BY-NC 4.0
  conversation.md       this file
  corpus/               output (test reel)
```
