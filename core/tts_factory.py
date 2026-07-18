from typing import Literal
from .tts_base import TTSBase


class TTSFactory:
    """Factory for creating TTS engines"""
    
    @staticmethod
    def create_engine(
        engine_type: Literal["local", "qwen3", "api"] = "local",
        api_url: str = "http://localhost:7778/v1"
    ) -> TTSBase:
        """
        Create a TTS engine.
        
        Args:
            engine_type: "local" for Chatterbox, "qwen3" for Faster Qwen3-TTS,
                or "api" for a remote server
            api_url: URL for API engine (ignored for local)
            
        Returns:
            TTSBase: TTS engine instance
        """
        if engine_type == "local":
            from .tts_engine_local import ChatterboxEngine
            return ChatterboxEngine()
        elif engine_type == "api":
            from .tts_engine_api import TTSEngineAPI
            return TTSEngineAPI(base_url=api_url)
        elif engine_type == "qwen3":
            from .tts_engine_qwen import Qwen3Engine
            return Qwen3Engine()
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
