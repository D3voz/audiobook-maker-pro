"""JSON-line worker for Faster Qwen3-TTS.

The worker owns the Qwen model and CUDA graphs in an isolated Python process.
Its stdout is reserved for protocol messages; library logs are redirected to
stderr so they cannot corrupt the protocol.
"""

from __future__ import annotations

import gc
import inspect
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path


PROTOCOL_OUTPUT = None
ACTIVE_REQUEST_ID = None

_model = None
_model_key = None


def send(payload: dict) -> None:
    if PROTOCOL_OUTPUT is None:
        raise RuntimeError("Worker protocol output is not initialized.")
    # ASCII JSON avoids Windows console-codepage corruption. User text and
    # Unicode status characters are preserved through JSON escapes.
    PROTOCOL_OUTPUT.write(json.dumps(payload, ensure_ascii=True) + "\n")
    PROTOCOL_OUTPUT.flush()


def send_event(message: str, percent: int | None = None) -> None:
    """Send a progress event while keeping stdout protocol-safe."""
    if ACTIVE_REQUEST_ID is None:
        return
    payload = {
        "id": ACTIVE_REQUEST_ID,
        "event": "progress",
        "message": message,
    }
    if percent is not None:
        payload["percent"] = max(0, min(100, int(percent)))
    send(payload)


def unload_model() -> None:
    global _model, _model_key
    if _model is not None:
        del _model
        _model = None
        _model_key = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


def get_model(request: dict):
    global _model, _model_key

    model_name = request["model"]
    dtype_name = request.get("data_type", "bfloat16")
    max_seq_len = int(request.get("max_seq_len", 2048))
    key = (model_name, dtype_name, max_seq_len)
    if _model is not None and _model_key == key:
        send_event("Reusing the loaded Qwen model and CUDA graphs...")
        return _model

    unload_model()

    if model_is_cached(model_name):
        send_event(f"Loading cached Qwen model · {short_model_name(model_name)}...")
    else:
        send_event(
            f"First use · downloading Qwen model · {short_model_name(model_name)}...",
            percent=0,
        )

    import torch
    from faster_qwen3_tts import FasterQwen3TTS

    dtype = getattr(torch, dtype_name)
    load_options = {
        "device": "cuda",
        "dtype": dtype,
        "attn_implementation": "sdpa",
        "max_seq_len": max_seq_len,
        # Supported by newer revisions; older CUDA-only releases do not need it.
        "backend": "torch",
    }
    _model = FasterQwen3TTS.from_pretrained(
        model_name,
        **compatible_kwargs(FasterQwen3TTS.from_pretrained, load_options),
    )
    send_event("Model files ready · capturing CUDA graphs...")
    warmup_model(_model, prefill_len=100)
    send_event("Qwen model and CUDA graphs are ready.")
    _model_key = key
    return _model


def compatible_kwargs(function, options: dict) -> dict:
    """Pass only keyword arguments understood by the installed engine API."""
    parameters = inspect.signature(function).parameters.values()
    if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters):
        return dict(options)
    names = {parameter.name for parameter in parameters}
    return {name: value for name, value in options.items() if name in names}


def warmup_model(model, prefill_len: int) -> None:
    """Support both the newer public warmup and the older private alias."""
    warmup = getattr(model, "warmup", None) or getattr(model, "_warmup", None)
    if warmup is None:
        raise RuntimeError("The installed Faster Qwen3-TTS model has no warmup method.")
    warmup(prefill_len=prefill_len)


def short_model_name(model_name: str) -> str:
    return model_name.rstrip("/\\").split("/")[-1].split("\\")[-1]


def model_is_cached(model_name: str) -> bool:
    """Best-effort check used only to choose first-run UI wording."""
    model_path = Path(model_name)
    if model_path.exists():
        return True
    try:
        from huggingface_hub.constants import HF_HUB_CACHE

        repo_folder = Path(HF_HUB_CACHE) / f"models--{model_name.replace('/', '--')}"
        snapshots = repo_folder / "snapshots"
        return snapshots.is_dir() and any(snapshots.iterdir())
    except Exception:
        return False


def sampling_options(request: dict) -> dict:
    return {
        "max_new_tokens": int(request.get("max_new_tokens", 2048)),
        "min_new_tokens": 2,
        "temperature": float(request.get("temperature", 0.9)),
        "top_k": int(request.get("top_k", 50)),
        "top_p": float(request.get("top_p", 1.0)),
        "do_sample": bool(request.get("do_sample", True)),
        "repetition_penalty": float(request.get("repetition_penalty", 1.05)),
    }


def generate(request: dict) -> dict:
    import numpy as np
    import soundfile as sf
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("Faster Qwen3-TTS CUDA graphs require an NVIDIA CUDA GPU.")

    seed = int(request.get("seed", -1))
    if seed >= 0:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    model = get_model(request)
    mode = request.get("mode", "clone")
    language = request.get("language", "Auto") or "Auto"
    options = sampling_options(request)
    streaming = bool(request.get("streaming", False))
    chunk_size = int(request.get("chunk_size", 8))

    if mode == "clone":
        method_name = "generate_voice_clone_streaming" if streaming else "generate_voice_clone"
        kwargs = {
            "text": request["text"],
            "language": language,
            "ref_audio": request.get("ref_audio"),
            "ref_text": request.get("ref_text", ""),
            "xvec_only": bool(request.get("xvec_only", False)),
            "append_silence": bool(request.get("append_silence", True)),
            "instruct": request.get("instruct") or None,
            **options,
        }
    elif mode == "custom":
        method_name = "generate_custom_voice_streaming" if streaming else "generate_custom_voice"
        kwargs = {
            "text": request["text"],
            "speaker": request.get("speaker", "Ryan"),
            "language": language,
            "instruct": request.get("instruct") or None,
            **options,
        }
    elif mode == "design":
        method_name = "generate_voice_design_streaming" if streaming else "generate_voice_design"
        kwargs = {
            "text": request["text"],
            "instruct": request.get("instruct", ""),
            "language": language,
            **options,
        }
    else:
        raise ValueError(f"Unsupported Qwen generation mode: {mode}")

    method = getattr(model, method_name)
    send_event(f"Generating speech · {mode.replace('_', ' ').title()}...")
    generation_started = time.perf_counter()
    if streaming:
        chunks = []
        sample_rate = None
        for audio_chunk, sample_rate, _timing in method(chunk_size=chunk_size, **kwargs):
            chunk = np.asarray(audio_chunk, dtype=np.float32).reshape(-1)
            if chunk.size:
                chunks.append(chunk)
        if not chunks or sample_rate is None:
            raise RuntimeError("Qwen returned no audio.")
        audio = np.concatenate(chunks)
    else:
        audio_arrays, sample_rate = method(**kwargs)
        chunks = [np.asarray(item, dtype=np.float32).reshape(-1) for item in audio_arrays]
        if not chunks:
            raise RuntimeError("Qwen returned no audio.")
        audio = np.concatenate(chunks)

    audio = np.nan_to_num(audio, copy=False)
    elapsed = max(time.perf_counter() - generation_started, 0.001)
    duration = audio.size / float(sample_rate)
    realtime_multiple = duration / elapsed
    steps_per_second = realtime_multiple * 12.0
    send_event(
        f"Generated {duration:.1f}s audio in {elapsed:.1f}s · "
        f"{steps_per_second:.1f} steps/s · {realtime_multiple:.2f}× real-time"
    )
    output_path = Path(request["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, int(sample_rate), format="WAV", subtype="PCM_16")
    return {"sample_rate": int(sample_rate), "samples": int(audio.size)}


def handle(message: dict) -> dict:
    command = message.get("command")
    if command == "ping":
        return {"ready": True, "pid": os.getpid()}
    if command == "generate":
        return generate(message["request"])
    if command == "unload":
        unload_model()
        return {"unloaded": True}
    if command == "shutdown":
        unload_model()
        return {"shutdown": True}
    raise ValueError(f"Unknown worker command: {command}")


def main() -> None:
    global ACTIVE_REQUEST_ID, PROTOCOL_OUTPUT
    PROTOCOL_OUTPUT = sys.stdout
    sys.stdout = sys.stderr
    logging.basicConfig(
        level=logging.INFO,
        format="[Qwen] %(message)s",
        stream=sys.stderr,
    )
    for line in sys.stdin:
        try:
            message = json.loads(line)
            request_id = message.get("id")
            ACTIVE_REQUEST_ID = request_id
            result = handle(message)
            send({"id": request_id, "ok": True, "result": result})
            if message.get("command") == "shutdown":
                break
        except Exception as exc:
            send(
                {
                    "id": locals().get("request_id"),
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        finally:
            ACTIVE_REQUEST_ID = None


if __name__ == "__main__":
    main()
