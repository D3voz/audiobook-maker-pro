"""
Local Chatterbox TTS Engine
Direct integration with the optimized Chatterbox inference package used by
the TTS-WebUI extension. TTS-WebUI itself is not imported or required.
Uses existing HuggingFace cache for models.
"""

from __future__ import annotations

import importlib.util
import inspect
import io
import os
from importlib import metadata

import torch
from typing import Optional
from pathlib import Path

from .tts_base import TTSBase


class ChatterboxEngine(TTSBase):
    """
    Local Chatterbox TTS engine.
    Uses the optimized Chatterbox package directly, without a WebUI server.
    Automatically uses HuggingFace cache.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the local Chatterbox engine.
        
        Args:
            cache_dir: Custom cache directory (optional, uses HF_HOME or default)
        """
        self.current_model = None
        self.current_device = None
        self.current_dtype = None
        self.model_name = None
        self.cached_voice_path = None
        self.supported_params = None  # Will be detected on first use
        self.optimized_backend_available = False
        
        # Set up cache directory
        if cache_dir:
            os.environ['HF_HOME'] = cache_dir
            os.environ['TRANSFORMERS_CACHE'] = cache_dir
        
        self.cache_info = self._get_cache_info()
        
    def _get_cache_info(self) -> dict:
        """Get information about HuggingFace cache"""
        hf_home = os.environ.get('HF_HOME')
        if not hf_home:
            if os.name == 'nt':  # Windows
                hf_home = os.path.join(os.environ.get('USERPROFILE', ''), '.cache', 'huggingface')
            else:  # Linux/Mac
                hf_home = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
        
        cache_path = Path(hf_home) / 'hub'
        
        # Check for existing Chatterbox models
        model_dirs = []
        if cache_path.exists():
            model_dirs = list(cache_path.glob('models--*--chatterbox*'))
        
        return {
            'cache_dir': str(cache_path),
            'existing_models': [d.name for d in model_dirs],
            'has_models': len(model_dirs) > 0
        }
    
    def generate_speech(
        self,
        text: str,
        model: str,
        voice: str,
        exaggeration: float,
        cfg_weight: float,
        temperature: float,
        seed: int,
        split_chunks: bool,
        halve_first_chunk: bool,
        desired_length: int,
        max_length: int,
        device: str,
        data_type: str,
        use_compilation: bool,
        max_new_tokens: int,
        cache_length: int,
        **engine_options
    ) -> bytes:
        """Generate speech using local Chatterbox model."""
        # NumPy and SciPy can stay lazy because they do not initialize the CUDA
        # runtime. Torch is initialized once on the app's startup thread; doing
        # its first import inside a short-lived QThread can corrupt native state
        # when that worker exits on Windows.
        import numpy as np
        
        print("=" * 60)
        print("Generating speech with local Chatterbox engine...")
        print(f"Model: {model}")
        print(f"Voice: {voice}")
        print(f"Text length: {len(text)} characters")
        print(f"Device: {device}, dtype: {data_type}")
        
        # Resolve device and dtype
        device_obj = self._resolve_device(device)
        dtype_obj = self._resolve_dtype(data_type)
        
        # Load or reuse model
        model_obj = self._get_model(model, device_obj, dtype_obj)
        
        # Detect supported parameters once. The optimized TTS-WebUI fork
        # exposes max_cache_len and t3_params.
        if self.supported_params is None:
            self.supported_params = self._get_supported_generate_params(model_obj)
            self.optimized_backend_available = {
                'max_cache_len', 't3_params'
            }.issubset(self.supported_params)
            print(f"Detected generate() parameters: {self.supported_params}")
            if device_obj.type == "cuda" and not self.optimized_backend_available:
                print(
                    "WARNING: The installed Chatterbox package does not expose "
                    "the optimized CUDA-graph backend. Reinstall requirements.txt "
                    "to get TTS-WebUI-equivalent local performance."
                )
        
        # Prepare voice conditioning
        if voice and os.path.exists(voice):
            if voice != self.cached_voice_path:
                print(f"Loading voice reference: {voice}")
                try:
                    model_obj.prepare_conditionals(voice, exaggeration=exaggeration)
                    if dtype_obj != torch.float32:
                        model_obj.conds.t3.to(dtype=dtype_obj)
                    self.cached_voice_path = voice
                    print("Voice loaded successfully")
                except Exception as e:
                    print(f"Warning: Could not load voice: {e}")
                    print("Continuing without voice reference...")
        elif voice:
            print(f"Warning: Voice file not found: {voice}")
            print("Continuing without voice reference...")
        
        # inference_mode avoids autograd bookkeeping and is the mode used by
        # the optimized Chatterbox implementation itself.
        with torch.inference_mode():
            audio_chunks = []
            
            # Handle text chunking
            if split_chunks:
                texts = self._split_text(text, desired_length, max_length)
                if halve_first_chunk and len(texts) > 0:
                    first_chunks = self._split_text(
                        texts[0], 
                        desired_length // 2, 
                        max_length // 2
                    )
                    texts = first_chunks + texts[1:]
            else:
                texts = [text]
            
            print(f"Processing {len(texts)} text chunk(s)...")
            
            # Set seed if specified
            if seed != -1:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
                print(f"Using seed: {seed}")
            
            for i, chunk in enumerate(texts):
                print(f"Generating chunk {i+1}/{len(texts)}: {chunk[:50]}...")
                
                # Build generation parameters based on what's supported.
                gen_params = self._build_generation_params(
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                    cache_length=cache_length,
                    device=device_obj,
                    use_compilation=use_compilation,
                )
                
                # Generate audio for this chunk
                try:
                    generated = model_obj.generate(chunk, **gen_params)
                    wav = self._last_waveform(generated)
                    audio_chunks.append(wav.squeeze().detach().cpu().numpy())
                        
                except Exception as e:
                    print(f"Error with current params: {e}")
                    raise Exception(f"Failed to generate chunk {i+1}: {str(e)}") from e
            
            # Combine all chunks
            if len(audio_chunks) > 1:
                full_audio = np.concatenate(audio_chunks, axis=0)
            elif len(audio_chunks) == 1:
                full_audio = audio_chunks[0]
            else:
                raise Exception("No audio generated")
            
            # Convert to WAV bytes
            wav_bytes = self._numpy_to_wav(full_audio, model_obj.sr)
            
            print(f"Generated {len(wav_bytes)} bytes of audio")
            print("=" * 60)
            
            return wav_bytes
    
    def test_connection(self) -> bool:
        """Check installation without importing Torch or the model package."""
        if importlib.util.find_spec("chatterbox") is None:
            print("Chatterbox module not found")
            return False

        package_version = "installed"
        for distribution_name in (
            "tts-webui.chatterbox-tts",
            "tts-webui-chatterbox-tts",
            "chatterbox-tts",
        ):
            try:
                package_version = metadata.version(distribution_name)
                break
            except metadata.PackageNotFoundError:
                continue

        print(f"Chatterbox module found · {package_version}")
        print(f"  Cache directory: {self.cache_info['cache_dir']}")
        print(f"  Existing models: {self.cache_info['existing_models']}")
        print("  Optimized backend validation is deferred until first generation")
        return True
    
    def cleanup(self):
        """Cleanup model and free GPU memory"""
        if self.current_model is not None:
            print("Cleaning up Chatterbox model...")
            del self.current_model
            self.current_model = None
            self.cached_voice_path = None
            self.supported_params = None
            self.optimized_backend_available = False
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("GPU cache cleared")
    
    def _get_model(self, model_name: str, device: torch.device, dtype: torch.dtype):
        """Load or reuse the Chatterbox model."""
        # Check if we can reuse existing model
        if (self.current_model is not None and 
            self.model_name == model_name and
            self.current_device == device and
            self.current_dtype == dtype):
            print("Reusing existing model from memory")
            return self.current_model
        
        # Load new model
        print(f"Loading {model_name} model...")
        print(f"Cache directory: {self.cache_info['cache_dir']}")
        
        try:
            if model_name == "multilingual":
                from chatterbox.mtl_tts import ChatterboxMultilingualTTS
                print("Loading ChatterboxMultilingualTTS...")
                model = ChatterboxMultilingualTTS.from_pretrained(device=device)
            else:
                from chatterbox.tts import ChatterboxTTS
                print("Loading ChatterboxTTS...")
                model = ChatterboxTTS.from_pretrained(device=device)
            
            print("Model loaded from HuggingFace cache")
            
            # Move to correct device and dtype
            model = self._chatterbox_tts_to(model, device, dtype)
            
            # Cache model info
            self.current_model = model
            self.model_name = model_name
            self.current_device = device
            self.current_dtype = dtype
            self.cached_voice_path = None
            self.supported_params = None
            
            print(f"Model ready on {device} with {dtype}")
            return model
            
        except Exception as e:
            raise Exception(
                f"Failed to load Chatterbox model:\n{str(e)}\n\n"
                f"Cache directory: {self.cache_info['cache_dir']}\n"
                f"Existing models: {self.cache_info['existing_models']}\n\n"
                f"Make sure Chatterbox is installed: pip install chatterbox-tts"
            )
    
    def _chatterbox_tts_to(self, model, device: torch.device, dtype: torch.dtype):
        """Move Chatterbox model to device and dtype"""
        print(f"Moving model to {device}, {dtype}")
        
        model.ve.to(device=device)
        
        # T3 to dtype
        model.t3.to(dtype=dtype)
        model.conds.t3.to(dtype=dtype)
        
        # S3gen handling
        if dtype == torch.float16:
            model.s3gen.flow.fp16 = True
        elif dtype == torch.float32:
            model.s3gen.flow.fp16 = False
        
        s3_dtype = dtype if dtype != torch.bfloat16 else torch.float16
        model.s3gen.to(dtype=s3_dtype)
        
        # Keep these at float32 to avoid cuFFT errors
        model.s3gen.mel2wav.to(dtype=torch.float32)
        model.s3gen.tokenizer.to(dtype=torch.float32)
        model.s3gen.speaker_encoder.to(dtype=torch.float32)
        
        model.device = device
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return model
    
    def _get_supported_generate_params(self, model) -> set:
        """
        Detect which parameters the model's generate() method supports.
        
        Args:
            model: The Chatterbox model instance
            
        Returns:
            set: Set of supported parameter names
        """
        try:
            generate_signature = inspect.signature(model.generate)
            params = set(generate_signature.parameters.keys())
            
            # Remove special parameters
            params.discard('self')
            params.discard('text')
            params.discard('args')
            params.discard('kwargs')
            
            print(f"Model.generate() signature: {generate_signature}")
            
            return params
        except Exception as e:
            print(f"Could not inspect generate() signature: {e}")
            # Return minimal safe set for base Chatterbox
            return {'exaggeration', 'cfg_weight', 'temperature'}
    
    def _build_generation_params(
        self, 
        exaggeration: float,
        cfg_weight: float,
        temperature: float,
        max_new_tokens: int,
        cache_length: int,
        device: torch.device,
        use_compilation: bool,
    ) -> dict:
        """
        Build generation parameters based on what the model supports.
        
        Returns:
            dict: Parameters to pass to model.generate()
        """
        gen_params = {}
        
        # Core parameters (usually supported)
        if 'exaggeration' in self.supported_params:
            gen_params['exaggeration'] = exaggeration
        
        if 'cfg_weight' in self.supported_params:
            gen_params['cfg_weight'] = cfg_weight
        
        if 'temperature' in self.supported_params:
            gen_params['temperature'] = temperature
        
        # Advanced parameters (may not be supported in base library)
        if 'max_new_tokens' in self.supported_params:
            gen_params['max_new_tokens'] = max_new_tokens
        
        if 'max_cache_len' in self.supported_params:
            gen_params['max_cache_len'] = cache_length
        
        # The optimized English model keeps language_id for API compatibility,
        # while the multilingual model requires it.
        if 'language_id' in self.supported_params:
            gen_params['language_id'] = "en"

        # Match the TTS-WebUI extension defaults. Its manual CUDA-graph token
        # loop provides the large speedup without requiring the WebUI server.
        # The existing compilation option controls only the initial forward
        # pass; token generation remains on the faster manual graph backend.
        if 't3_params' in self.supported_params:
            is_cuda = device.type == 'cuda'
            gen_params['t3_params'] = {
                'initial_forward_pass_backend': (
                    'cudagraphs' if is_cuda and use_compilation else 'eager'
                ),
                'generate_token_backend': (
                    'cudagraphs-manual' if is_cuda else 'eager'
                ),
            }
        
        print(f"Generation params: {gen_params}")
        return gen_params

    def _last_waveform(self, generated):
        """Normalize tensor and streaming Chatterbox generation results."""
        if torch.is_tensor(generated):
            return generated

        wav = None
        for wav_chunk in generated:
            wav = wav_chunk

        if wav is None:
            raise RuntimeError("Chatterbox returned no audio")
        return wav
    
    def _resolve_device(self, device: str) -> torch.device:
        """Resolve device string to torch.device"""
        if device == "auto":
            if torch.cuda.is_available():
                selected = torch.device("cuda")
                print(f"Auto-selected device: cuda")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                selected = torch.device("mps")
                print(f"Auto-selected device: mps (Apple Silicon)")
            else:
                selected = torch.device("cpu")
                print(f"Auto-selected device: cpu")
            return selected
        return torch.device(device)
    
    def _resolve_dtype(self, dtype: str) -> torch.dtype:
        """Resolve dtype string to torch.dtype"""
        dtype_map = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        return dtype_map.get(dtype, torch.float32)
    
    def _split_text(self, text: str, desired_length: int, max_length: int) -> list:
        """
        Split text into chunks.
        Uses the advanced splitter if available, otherwise falls back to simple splitting.
        """
        # Try to import the better splitter
        try:
            from .text_splitter import split_and_recombine_text
            return split_and_recombine_text(text, desired_length, max_length)
        except ImportError:
            pass
        
        # Fallback: simple sentence-based splitting
        # Split on sentence endings
        sentences = []
        for ending in ['. ', '! ', '? ']:
            text = text.replace(ending, ending + '|SPLIT|')
        
        raw_sentences = text.split('|SPLIT|')
        
        chunks = []
        current_chunk = ""
        
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed desired length
            if len(current_chunk) + len(sentence) + 1 < desired_length:
                current_chunk += sentence + " "
            else:
                # If we have a current chunk, save it
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk
                # If single sentence is too long, we still need to include it
                if len(sentence) > max_length:
                    # Split long sentence at commas or spaces
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 < max_length:
                            temp_chunk += word + " "
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                    current_chunk = temp_chunk
                else:
                    current_chunk = sentence + " "
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def _numpy_to_wav(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy array to WAV bytes"""
        import numpy as np
        from scipy.io import wavfile

        output_buffer = io.BytesIO()
        
        # Ensure audio is in correct format for WAV
        if audio.dtype != np.int16:
            # Chatterbox usually outputs float32 in range [-1, 1]
            if audio.dtype in [np.float32, np.float64]:
                # Clip to valid range
                audio = np.clip(audio, -1.0, 1.0)
                # Convert to int16
                audio = (audio * 32767).astype(np.int16)
        
        wavfile.write(output_buffer, sample_rate, audio)
        return output_buffer.getvalue()
