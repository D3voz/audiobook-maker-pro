import io
import json
import sys
import wave
from pathlib import Path

import pytest

from core.qwen_runtime import QwenRuntimeManager
from core.tts_engine_qwen import Qwen3Engine, QwenWorkerClient
from core.tts_factory import TTSFactory
from engine_runtimes.qwen3.worker import compatible_kwargs, warmup_model


def make_wav(sample_rate=24000, frames=240):
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"\x00\x00" * frames)
    return output.getvalue()


class FakeRuntime:
    worker_script = Path(__file__)

    def is_installed(self):
        return True


class FakeClient:
    requests = []

    def __init__(self, runtime):
        self.runtime = runtime

    def generate(self, request, progress_callback=None):
        self.requests.append(request)
        if progress_callback:
            progress_callback("Generated 1.0s audio in 0.5s · 24.0 steps/s")
        return make_wav()

    def close(self):
        pass


def test_qwen_voice_clone_maps_engine_settings(tmp_path):
    FakeClient.requests = []
    reference = tmp_path / "reference.wav"
    reference.write_bytes(make_wav())
    engine = Qwen3Engine(FakeRuntime(), FakeClient)

    progress = []
    audio = engine.generate_speech(
        "Hello from Qwen.",
        qwen_mode="clone",
        qwen_model="Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        qwen_language="English",
        qwen_ref_text="This is the reference.",
        qwen_xvec_only=False,
        qwen_append_silence=True,
        qwen_top_k=40,
        qwen_top_p=0.95,
        qwen_repetition_penalty=1.08,
        qwen_max_seq_len=2048,
        qwen_streaming=True,
        qwen_stream_chunk_size=12,
        voice=str(reference),
        data_type="bfloat16",
        temperature=0.85,
        seed=123,
        max_new_tokens=1500,
        split_chunks=False,
        _progress_callback=progress.append,
    )

    assert audio.startswith(b"RIFF")
    request = FakeClient.requests[0]
    assert request["mode"] == "clone"
    assert request["model"].endswith("0.6B-Base")
    assert request["ref_audio"] == str(reference)
    assert request["ref_text"] == "This is the reference."
    assert request["streaming"] is True
    assert request["chunk_size"] == 12
    assert request["seed"] == 123
    assert progress == ["Generated 1.0s audio in 0.5s · 24.0 steps/s"]


def test_qwen_full_clone_requires_reference_transcript(tmp_path):
    reference = tmp_path / "reference.wav"
    reference.write_bytes(make_wav())
    engine = Qwen3Engine(FakeRuntime(), FakeClient)

    with pytest.raises(ValueError, match="reference transcript"):
        engine.generate_speech(
            "Hello",
            qwen_mode="clone",
            voice=str(reference),
            qwen_ref_text="",
            qwen_xvec_only=False,
            split_chunks=False,
        )


def test_qwen_runtime_marker_controls_installed_state(tmp_path):
    manager = QwenRuntimeManager(runtime_root=tmp_path)
    manager.runtime_dir.mkdir(parents=True)
    manager.python_executable.parent.mkdir(parents=True, exist_ok=True)
    manager.python_executable.write_text("", encoding="utf-8")
    manager.marker_path.write_text(
        json.dumps(
            {
                "engine": manager.ENGINE_ID,
                "package_version": manager.PACKAGE_VERSION,
                "source_commit": manager.SOURCE_COMMIT,
            }
        ),
        encoding="utf-8",
    )

    assert manager.is_installed()

    marker = json.loads(manager.marker_path.read_text(encoding="utf-8"))
    marker["package_version"] = "old"
    manager.marker_path.write_text(json.dumps(marker), encoding="utf-8")
    assert not manager.is_installed()


def test_qwen_worker_protocol_ping(tmp_path):
    class WorkerRuntime:
        python_executable = Path(sys.executable)
        worker_script = (
            Path(__file__).resolve().parents[1]
            / "engine_runtimes"
            / "qwen3"
            / "worker.py"
        )
        temp_dir = tmp_path

        @staticmethod
        def is_installed():
            return True

    client = QwenWorkerClient(WorkerRuntime())
    try:
        assert client.ping()
    finally:
        client.close()


def test_factory_creates_qwen_without_importing_engine_dependencies():
    engine = TTSFactory.create_engine("qwen3")
    assert isinstance(engine, Qwen3Engine)
    engine.cleanup()


def test_runtime_retry_reuses_completed_installation(tmp_path, monkeypatch):
    manager = QwenRuntimeManager(runtime_root=tmp_path)
    manager.python_executable.parent.mkdir(parents=True, exist_ok=True)
    manager.python_executable.write_text("", encoding="utf-8")
    verified = []
    monkeypatch.setattr(
        manager,
        "_verify_runtime",
        lambda progress, stage: verified.append(stage),
    )

    manager.install()

    assert verified == ["Checking the existing Qwen runtime..."]
    assert manager.is_installed()


def test_worker_adapts_to_legacy_loader_and_warmup_api():
    def legacy_loader(model_name, device, dtype, attn_implementation, max_seq_len):
        return None

    options = {
        "device": "cuda",
        "dtype": "bfloat16",
        "attn_implementation": "sdpa",
        "max_seq_len": 2048,
        "backend": "torch",
    }
    assert compatible_kwargs(legacy_loader, options) == {
        key: value for key, value in options.items() if key != "backend"
    }

    class LegacyModel:
        warmed = None

        def _warmup(self, prefill_len):
            self.warmed = prefill_len

    model = LegacyModel()
    warmup_model(model, 100)
    assert model.warmed == 100


def test_client_formats_huggingface_download_progress():
    message = "model.safetensors: 42%|####      | 420M/1.00G [00:04<00:06, 96MB/s]"
    client = QwenWorkerClient(FakeRuntime())
    assert client._format_download_progress(message) == (
        "Downloading Qwen model · model.safetensors: 42%"
    )

    client._model_files_cached = True
    assert client._format_download_progress(message) == (
        "Checking cached Qwen model · model.safetensors: 42%"
    )


def test_client_forwards_structured_worker_progress(tmp_path):
    worker_script = tmp_path / "event_worker.py"
    worker_script.write_text(
        "import json, sys\n"
        "for line in sys.stdin:\n"
        "    message = json.loads(line)\n"
        "    request_id = message['id']\n"
        "    if message['command'] == 'ping':\n"
        "        print(json.dumps({'id': request_id, 'event': 'progress', "
        "'message': 'Loading cached Qwen model...'}), flush=True)\n"
        "    print(json.dumps({'id': request_id, 'ok': True, "
        "'result': {'ready': True}}), flush=True)\n"
        "    if message['command'] == 'shutdown':\n"
        "        break\n",
        encoding="utf-8",
    )

    class EventRuntime:
        python_executable = Path(sys.executable)
        temp_dir = tmp_path

        @property
        def worker_script(self):
            return worker_script

        @staticmethod
        def is_installed():
            return True

    progress = []
    client = QwenWorkerClient(EventRuntime())
    try:
        result = client._request("ping", progress_callback=progress.append)
    finally:
        client.close()

    assert result["ready"] is True
    assert progress == ["Loading cached Qwen model..."]
