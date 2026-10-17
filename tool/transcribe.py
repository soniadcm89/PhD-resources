"""Local transcription with faster-whisper (GPU if available, else CPU int8)."""
import os
import site
from dataclasses import dataclass, field
from pathlib import Path


def _register_nvidia_dlls() -> None:
    """Make pip-installed CUDA libs (cuBLAS/cuDNN) findable on Windows."""
    if os.name != "nt":
        return
    roots = set(site.getsitepackages() + [site.getusersitepackages()])
    for root in roots:
        for bin_dir in Path(root, "nvidia").glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


_register_nvidia_dlls()

import ctranslate2  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    segments: list[Segment]
    language: str
    language_probability: float
    language_forced: bool
    model: str
    device: str
    compute_type: str
    duration_seconds: float = 0.0
    extra: dict = field(default_factory=dict)


class Transcriber:
    """Loads the model once and reuses it across reels (batch mode)."""

    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self._model = None
        self.device = None
        self.compute_type = None
        self._load(self._pick_device())

    @staticmethod
    def _pick_device() -> tuple[str, str]:
        try:
            if ctranslate2.get_cuda_device_count() > 0:
                return "cuda", "float16"
        except Exception:
            pass
        return "cpu", "int8"

    def _load(self, choice: tuple[str, str]) -> None:
        self.device, self.compute_type = choice
        self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def _run(self, audio: str, language: str | None) -> TranscriptionResult:
        gen, info = self._model.transcribe(audio, language=language)
        segments = [Segment(s.start, s.end, s.text.strip()) for s in gen if s.text.strip()]
        return TranscriptionResult(
            segments=segments,
            language=info.language,
            language_probability=round(float(info.language_probability), 4),
            language_forced=language is not None,
            model=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            duration_seconds=round(float(info.duration), 2),
        )

    def transcribe(self, audio_path: Path, language: str | None = None) -> TranscriptionResult:
        try:
            return self._run(str(audio_path), language)
        except Exception:
            if self.device != "cuda":
                raise
            # CUDA runtime problem: fall back to CPU/int8 and retry once.
            print("  GPU failed, falling back to CPU (int8)")
            self._load(("cpu", "int8"))
            return self._run(str(audio_path), language)


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    return f"[{total // 60:02d}:{total % 60:02d}]"
