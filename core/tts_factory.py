from typing import Literal
from .tts_base import TTSBase
from .tts_engine_api import TTSEngineAPI
from .tts_engine_local import ChatterboxEngine


class TTSFactory:
    """Factory for creating TTS engines"""
    
    @staticmethod
    def create_engine(
        engine_type: Literal["local", "api"] = "local",
        api_url: str = "http://localhost:7778/v1"
    ) -> TTSBase:
        """
        Create a TTS engine.
        
        Args:
            engine_type: "local" for direct Chatterbox, "api" for remote server
            api_url: URL for API engine (ignored for local)
            
        Returns:
            TTSBase: TTS engine instance
        """
        if engine_type == "local":
            return ChatterboxEngine()
        elif engine_type == "api":
            return TTSEngineAPI(base_url=api_url)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")