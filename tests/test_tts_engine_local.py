"""Focused tests for the optimized local Chatterbox engine."""

import unittest
from unittest.mock import patch

import torch

from core.tts_engine_local import ChatterboxEngine


class OptimizedModelStub:
    sr = 24000

    def __init__(self):
        self.calls = []

    def generate(
        self,
        text,
        language_id=None,
        exaggeration=0.5,
        cfg_weight=0.5,
        temperature=0.8,
        max_new_tokens=1000,
        max_cache_len=1500,
        t3_params=None,
    ):
        self.calls.append(
            {
                "text": text,
                "language_id": language_id,
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
                "temperature": temperature,
                "max_new_tokens": max_new_tokens,
                "max_cache_len": max_cache_len,
                "t3_params": t3_params,
            }
        )
        return torch.tensor([[0.0, 0.25, -0.25]], dtype=torch.float32)


class TestOptimizedLocalEngine(unittest.TestCase):
    def test_cuda_generation_uses_tts_webui_optimized_backend(self):
        engine = ChatterboxEngine()
        model = OptimizedModelStub()

        with (
            patch.object(engine, "_resolve_device", return_value=torch.device("cuda")),
            patch.object(engine, "_resolve_dtype", return_value=torch.float16),
            patch.object(engine, "_get_model", return_value=model),
        ):
            audio = engine.generate_speech(
                text="A short test.",
                model="chatterbox",
                voice="",
                exaggeration=0.7,
                cfg_weight=0.4,
                temperature=0.8,
                seed=-1,
                split_chunks=False,
                halve_first_chunk=False,
                desired_length=200,
                max_length=300,
                device="cuda",
                data_type="float16",
                use_compilation=False,
                max_new_tokens=600,
                cache_length=700,
            )

        self.assertEqual(audio[:4], b"RIFF")
        self.assertEqual(model.calls[0]["language_id"], "en")
        self.assertEqual(model.calls[0]["exaggeration"], 0.7)
        self.assertEqual(model.calls[0]["max_cache_len"], 700)
        self.assertEqual(
            model.calls[0]["t3_params"],
            {
                "initial_forward_pass_backend": "eager",
                "generate_token_backend": "cudagraphs-manual",
            },
        )

    def test_non_cuda_generation_uses_eager_backend(self):
        engine = ChatterboxEngine()
        engine.supported_params = {
            "exaggeration",
            "cfg_weight",
            "temperature",
            "max_new_tokens",
            "max_cache_len",
            "language_id",
            "t3_params",
        }

        params = engine._build_generation_params(
            exaggeration=0.5,
            cfg_weight=0.5,
            temperature=0.8,
            max_new_tokens=1000,
            cache_length=1500,
            device=torch.device("cpu"),
            use_compilation=True,
        )

        self.assertEqual(
            params["t3_params"],
            {
                "initial_forward_pass_backend": "eager",
                "generate_token_backend": "eager",
            },
        )


if __name__ == "__main__":
    unittest.main()
