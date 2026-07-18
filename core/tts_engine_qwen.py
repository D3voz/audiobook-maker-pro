"""Faster Qwen3-TTS adapter backed by an isolated persistent worker."""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import uuid
import wave
from collections import deque
from pathlib import Path
from typing import Callable, Optional

from .qwen_runtime import QwenRuntimeManager
from .tts_base import TTSBase


class QwenRuntimeNotInstalled(RuntimeError):
    pass


class QwenWorkerClient:
    """Synchronous client for the long-lived Qwen subprocess."""

    def __init__(self, runtime_manager: QwenRuntimeManager):
        self.runtime = runtime_manager
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()
        self._stderr_tail = deque(maxlen=40)
        self._stderr_thread = None
        self._progress_callback = None
        self._last_download_message = None
        self._model_files_cached = False

    def generate(self, request: dict, progress_callback=None) -> bytes:
        self.runtime.temp_dir.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            prefix="qwen-",
            suffix=".wav",
            dir=self.runtime.temp_dir,
            delete=False,
        )
        output_path = Path(handle.name)
        handle.close()
        try:
            request = dict(request)
            request["output_path"] = str(output_path)
            self._request(
                "generate",
                request=request,
                progress_callback=progress_callback,
            )
            if not output_path.is_file() or output_path.stat().st_size == 0:
                raise RuntimeError("The Qwen worker did not produce an audio file.")
            return output_path.read_bytes()
        finally:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass

    def ping(self) -> bool:
        try:
            result = self._request("ping")
            return bool(result.get("ready"))
        except Exception:
            return False

    def close(self) -> None:
        with self._lock:
            process = self.process
            if process is None:
                return
            try:
                if process.poll() is None:
                    self._request("shutdown")
                    process.wait(timeout=5)
            except Exception:
                if process.poll() is None:
                    process.terminate()
            finally:
                self.process = None

    def _start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        if not self.runtime.is_installed():
            raise QwenRuntimeNotInstalled(
                "Faster Qwen3-TTS is not installed. Select the Qwen engine and "
                "click Install Engine first."
            )
        if not self.runtime.worker_script.is_file():
            raise RuntimeError(f"Qwen worker is missing: {self.runtime.worker_script}")

        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["TOKENIZERS_PARALLELISM"] = "false"
        self._stderr_tail.clear()
        self.process = subprocess.Popen(
            [str(self.runtime.python_executable), "-u", str(self.runtime.worker_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=environment,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

    def _drain_stderr(self) -> None:
        process = self.process
        if process is None or process.stderr is None:
            return
        buffer = []
        while True:
            character = process.stderr.read(1)
            if not character:
                break
            if character in ("\r", "\n"):
                line = "".join(buffer)
                buffer.clear()
                self._forward_stderr_line(line, character)
            else:
                buffer.append(character)
        if buffer:
            self._forward_stderr_line("".join(buffer), "\n")

    def _forward_stderr_line(self, line: str, delimiter: str) -> None:
        clean = self._strip_terminal_codes(line).strip()
        if clean:
            self._stderr_tail.append(clean)
            download_message = self._format_download_progress(clean)
            if download_message and download_message != self._last_download_message:
                self._last_download_message = download_message
                self._emit_progress(download_message, echo_to_terminal=False)

        # Preserve detailed library output, tqdm percentages, and timing logs.
        if line:
            self._safe_stream_write(sys.stderr, line + delimiter)

    def _request(self, command: str, progress_callback=None, **payload) -> dict:
        with self._lock:
            previous_callback = self._progress_callback
            self._progress_callback = progress_callback
            self._last_download_message = None
            try:
                self._start()
                assert self.process is not None
                assert self.process.stdin is not None
                assert self.process.stdout is not None

                request_id = uuid.uuid4().hex
                message = {"id": request_id, "command": command, **payload}
                try:
                    self.process.stdin.write(json.dumps(message, ensure_ascii=True) + "\n")
                    self.process.stdin.flush()
                except (BrokenPipeError, OSError) as exc:
                    raise RuntimeError(
                        self._worker_failure("Qwen worker stopped unexpectedly.")
                    ) from exc

                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        raise RuntimeError(
                            self._worker_failure("Qwen worker stopped unexpectedly.")
                        )
                    try:
                        response = json.loads(line)
                    except ValueError as exc:
                        raise RuntimeError(
                            f"Invalid response from Qwen worker: {line[:200]}"
                        ) from exc

                    if response.get("id") != request_id:
                        raise RuntimeError("Qwen worker returned an out-of-order response.")
                    if response.get("event") == "progress":
                        self._emit_progress(response.get("message", "Qwen is working..."))
                        continue
                    if not response.get("ok"):
                        error_message = response.get("error", "Qwen generation failed.")
                        raise RuntimeError(self._worker_failure(error_message))
                    return response.get("result", {})
            finally:
                self._progress_callback = previous_callback

    def _emit_progress(self, message: str, echo_to_terminal: bool = True) -> None:
        if message.startswith("Loading cached Qwen model"):
            self._model_files_cached = True
        elif message.startswith("First use"):
            self._model_files_cached = False
        if echo_to_terminal:
            self._safe_stream_write(sys.stdout, f"[Qwen] {message}\n")
        callback = self._progress_callback
        if callback:
            try:
                callback(message)
            except Exception:
                pass

    @staticmethod
    def _safe_stream_write(stream, message: str) -> None:
        """Never let a Windows terminal codepage interrupt generation."""
        try:
            stream.write(message)
        except UnicodeEncodeError:
            encoding = getattr(stream, "encoding", None) or "utf-8"
            safe = message.encode(encoding, errors="replace").decode(encoding)
            stream.write(safe)
        stream.flush()

    @staticmethod
    def _strip_terminal_codes(message: str) -> str:
        return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", message)

    def _format_download_progress(self, message: str) -> Optional[str]:
        clean = self._strip_terminal_codes(message).strip()
        match = re.search(r"(?<!\d)(\d{1,3})%\|", clean)
        if not match:
            return None
        percent = min(100, int(match.group(1)))
        description = clean[:match.start()].rstrip(" :")
        if len(description) > 42:
            description = "…" + description[-41:]
        activity = (
            "Checking cached Qwen model"
            if self._model_files_cached
            else "Downloading Qwen model"
        )
        if description:
            return f"{activity} · {description}: {percent}%"
        return f"{activity}: {percent}%"

    def _worker_failure(self, message: str) -> str:
        if not self._stderr_tail:
            return message
        details = "\n".join(list(self._stderr_tail)[-8:])
        return f"{message}\n\nEngine details:\n{details}"


class Qwen3Engine(TTSBase):
    """Faster Qwen3-TTS with CUDA graphs and a reusable model process."""

    def __init__(
        self,
        runtime_manager: Optional[QwenRuntimeManager] = None,
        client_factory: Callable[[QwenRuntimeManager], QwenWorkerClient] = QwenWorkerClient,
    ):
        self.runtime = runtime_manager or QwenRuntimeManager()
        self._client_factory = client_factory
        self._client = None

    def generate_speech(self, text: str, **settings) -> bytes:
        if not text.strip():
            raise ValueError("Enter some text before generating audio.")
        if not self.runtime.is_installed():
            raise QwenRuntimeNotInstalled(
                "Faster Qwen3-TTS is not installed. Click Install Engine in the "
                "TTS Engine panel, then try again."
            )

        mode = settings.get("qwen_mode", "clone")
        voice = (settings.get("voice") or settings.get("qwen_reference_audio") or "").strip()
        ref_text = (settings.get("qwen_ref_text") or "").strip()
        xvec_only = bool(settings.get("qwen_xvec_only", False))
        instruct = (settings.get("qwen_instruct") or "").strip()
        progress_callback = settings.get("_progress_callback")

        if mode == "clone":
            if not voice or not Path(voice).is_file():
                raise ValueError("Voice Clone mode needs a valid reference audio file.")
            if not xvec_only and not ref_text:
                raise ValueError(
                    "Full-fidelity voice cloning needs the reference transcript. "
                    "Add it, or enable Speaker embedding only."
                )
        elif mode == "custom" and not (settings.get("qwen_speaker") or "").strip():
            raise ValueError("Custom Voice mode needs a speaker selection.")
        elif mode == "design" and not instruct:
            raise ValueError("Voice Design mode needs a voice description.")

        request = {
            "mode": mode,
            "model": settings.get("qwen_model") or settings.get("model"),
            "text": text,
            "language": settings.get("qwen_language", "Auto"),
            "data_type": settings.get("data_type", "bfloat16"),
            "max_seq_len": int(settings.get("qwen_max_seq_len", 2048)),
            "ref_audio": voice or None,
            "ref_text": ref_text,
            "xvec_only": xvec_only,
            "append_silence": bool(settings.get("qwen_append_silence", True)),
            "speaker": settings.get("qwen_speaker", "Ryan"),
            "instruct": instruct,
            "temperature": float(settings.get("temperature", 0.9)),
            "top_k": int(settings.get("qwen_top_k", 50)),
            "top_p": float(settings.get("qwen_top_p", 1.0)),
            "do_sample": bool(settings.get("qwen_do_sample", True)),
            "repetition_penalty": float(settings.get("qwen_repetition_penalty", 1.05)),
            "max_new_tokens": int(settings.get("max_new_tokens", 2048)),
            "seed": int(settings.get("seed", -1)),
            "streaming": bool(settings.get("qwen_streaming", False)),
            "chunk_size": int(settings.get("qwen_stream_chunk_size", 8)),
        }

        chunks = self._split_text(text, settings)
        audio_segments = []
        for index, chunk in enumerate(chunks, start=1):
            chunk_request = dict(request)
            chunk_request["text"] = chunk
            chunk_callback = progress_callback
            if progress_callback and len(chunks) > 1:
                chunk_callback = lambda message, current=index: progress_callback(
                    f"Qwen chunk {current}/{len(chunks)} · {message}"
                )
            audio_segments.append(
                self._get_client().generate(
                    chunk_request,
                    progress_callback=chunk_callback,
                )
            )
        return self._combine_wav_segments(audio_segments)

    def test_connection(self) -> bool:
        return self.runtime.is_installed() and self.runtime.worker_script.is_file()

    def cleanup(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def _get_client(self) -> QwenWorkerClient:
        if self._client is None:
            self._client = self._client_factory(self.runtime)
        return self._client

    @staticmethod
    def _split_text(text: str, settings: dict) -> list[str]:
        if not settings.get("split_chunks", True):
            return [text]

        from .text_splitter import split_and_recombine_text

        desired = int(settings.get("desired_length", 200))
        maximum = int(settings.get("max_length", 300))
        chunks = split_and_recombine_text(text, desired, maximum)
        if settings.get("halve_first_chunk") and chunks:
            first = split_and_recombine_text(
                chunks[0], max(25, desired // 2), max(50, maximum // 2)
            )
            chunks = first + chunks[1:]
        return chunks or [text]

    @staticmethod
    def _combine_wav_segments(segments: list[bytes]) -> bytes:
        if not segments:
            raise RuntimeError("Qwen returned no audio segments.")
        if len(segments) == 1:
            return segments[0]

        params = None
        frames = []
        for segment in segments:
            with wave.open(io.BytesIO(segment), "rb") as reader:
                current = (
                    reader.getnchannels(),
                    reader.getsampwidth(),
                    reader.getframerate(),
                    reader.getcomptype(),
                )
                if params is None:
                    params = current
                elif current != params:
                    raise RuntimeError("Qwen audio segments use incompatible WAV formats.")
                frames.append(reader.readframes(reader.getnframes()))

        output = io.BytesIO()
        assert params is not None
        with wave.open(output, "wb") as writer:
            writer.setnchannels(params[0])
            writer.setsampwidth(params[1])
            writer.setframerate(params[2])
            writer.setcomptype(params[3], "not compressed")
            for frame_data in frames:
                writer.writeframes(frame_data)
        return output.getvalue()
