"""Managed, isolated runtime for the optional Faster Qwen3-TTS engine."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Callable, Optional


ProgressCallback = Optional[Callable[[str], None]]


class QwenRuntimeManager:
    """Create and inspect the engine-specific Python environment."""

    ENGINE_ID = "faster-qwen3-tts"
    # The pinned source currently retains the 0.2.6 distribution metadata even
    # though it contains commits newer than the PyPI 0.2.6 release.
    PACKAGE_VERSION = "0.2.6"
    SOURCE_COMMIT = "7cdef7e40195108b51a808f2ce5c7d5f3e235a79"
    SOURCE_URL = (
        "https://github.com/andimarafioti/faster-qwen3-tts/archive/"
        f"{SOURCE_COMMIT}.zip"
    )
    TORCH_VERSION = "2.11.0"
    TORCH_INDEX_URL = "https://download.pytorch.org/whl/cu128"

    def __init__(self, runtime_root: Optional[Path] = None):
        if runtime_root is None:
            override = os.environ.get("AUDIOBOOK_MAKER_RUNTIME_DIR")
            if override:
                runtime_root = Path(override)
            else:
                local_data = os.environ.get("LOCALAPPDATA")
                base = Path(local_data) if local_data else Path.home() / ".local" / "share"
                runtime_root = base / "AudiobookMakerPro" / "runtimes"

        self.runtime_root = Path(runtime_root)
        self.runtime_dir = self.runtime_root / "qwen3"
        self.marker_path = self.runtime_dir / "runtime.json"
        self.temp_dir = self.runtime_dir / "temp"

    @property
    def python_executable(self) -> Path:
        if os.name == "nt":
            return self.runtime_dir / "Scripts" / "python.exe"
        return self.runtime_dir / "bin" / "python"

    @property
    def worker_script(self) -> Path:
        return (
            Path(__file__).resolve().parent.parent
            / "engine_runtimes"
            / "qwen3"
            / "worker.py"
        )

    def is_installed(self) -> bool:
        if not self.python_executable.is_file() or not self.marker_path.is_file():
            return False

        try:
            marker = json.loads(self.marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False

        return (
            marker.get("engine") == self.ENGINE_ID
            and marker.get("package_version") == self.PACKAGE_VERSION
            and marker.get("source_commit") == self.SOURCE_COMMIT
        )

    def status_text(self) -> str:
        if self.is_installed():
            return f"Installed · Faster Qwen3-TTS {self.PACKAGE_VERSION}"
        return "Not installed · installed separately from Chatterbox"

    def install(self, progress: ProgressCallback = None) -> None:
        """Install the runtime. Intended to run from a background thread."""
        if sys.version_info < (3, 10):
            raise RuntimeError("Faster Qwen3-TTS requires Python 3.10 or newer.")

        self.runtime_root.mkdir(parents=True, exist_ok=True)

        # A previous attempt may have installed everything and failed only at
        # final verification. Reuse it instead of downloading CUDA again.
        if self.python_executable.is_file():
            try:
                self._verify_runtime(progress, "Checking the existing Qwen runtime...")
            except RuntimeError:
                pass
            else:
                self._write_marker()
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                self._emit(progress, "Faster Qwen3-TTS is ready. Models download on first use.")
                return

        self.marker_path.unlink(missing_ok=True)
        self._emit(progress, "Creating the isolated Qwen engine environment...")
        venv.EnvBuilder(with_pip=True, clear=False).create(self.runtime_dir)

        python = str(self.python_executable)
        self._run(
            [python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            progress,
            "Preparing the package installer...",
        )
        self._run(
            [
                python,
                "-m",
                "pip",
                "install",
                f"torch=={self.TORCH_VERSION}",
                f"torchaudio=={self.TORCH_VERSION}",
                "--index-url",
                self.TORCH_INDEX_URL,
            ],
            progress,
            "Installing the CUDA runtime (this is the largest download)...",
        )
        self._run(
            [
                python,
                "-m",
                "pip",
                "install",
                f"faster-qwen3-tts @ {self.SOURCE_URL}",
            ],
            progress,
            "Installing Faster Qwen3-TTS...",
        )
        self._verify_runtime(progress, "Verifying the engine runtime...")
        self._write_marker()
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._emit(progress, "Faster Qwen3-TTS is ready. Models download on first use.")

    def _verify_runtime(self, progress: ProgressCallback, stage: str) -> None:
        required_api = {
            "from_pretrained": {
                "model_name", "device", "dtype", "attn_implementation", "max_seq_len",
            },
            "generate_voice_clone": {
                "text", "language", "ref_audio", "ref_text", "xvec_only",
                "append_silence", "instruct",
            },
            "generate_voice_clone_streaming": {"chunk_size"},
            "generate_custom_voice": {"text", "speaker", "language", "instruct"},
            "generate_custom_voice_streaming": {"chunk_size"},
            "generate_voice_design": {"text", "instruct", "language"},
            "generate_voice_design_streaming": {"chunk_size"},
        }
        code = (
            "import importlib.metadata as m, inspect, json; "
            "from faster_qwen3_tts import FasterQwen3TTS; "
            "d=m.distribution('faster-qwen3-tts'); "
            "u=json.loads(d.read_text('direct_url.json') or '{}').get('url',''); "
            f"assert '{self.SOURCE_COMMIT}' in u, 'Pinned source commit is missing'; "
            f"r={required_api!r}; "
            "missing={n: sorted(p-set(inspect.signature(getattr(FasterQwen3TTS,n)).parameters)) "
            "for n,p in r.items()}; "
            "assert not any(missing.values()), 'Missing Qwen API parameters: '+str(missing); "
            "assert hasattr(FasterQwen3TTS,'warmup') or hasattr(FasterQwen3TTS,'_warmup'), "
            "'Missing Qwen warmup API'; "
            "print('Runtime verified: '+m.version('faster-qwen3-tts'))"
        )
        self._run(
            [str(self.python_executable), "-c", code],
            progress,
            stage,
        )

    def _write_marker(self) -> None:
        marker = {
            "engine": self.ENGINE_ID,
            "package_version": self.PACKAGE_VERSION,
            "source_commit": self.SOURCE_COMMIT,
            "torch_version": self.TORCH_VERSION,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        }
        self.marker_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")

    def _run(self, command: list[str], progress: ProgressCallback, stage: str) -> None:
        self._emit(progress, stage)
        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        recent_lines = []
        assert process.stdout is not None
        for line in process.stdout:
            clean = line.strip()
            if clean:
                recent_lines.append(clean)
                recent_lines = recent_lines[-12:]

        return_code = process.wait()
        if return_code != 0:
            details = "\n".join(recent_lines[-8:])
            raise RuntimeError(f"{stage} failed.\n\n{details}")

    @staticmethod
    def _emit(progress: ProgressCallback, message: str) -> None:
        if progress:
            progress(message)
