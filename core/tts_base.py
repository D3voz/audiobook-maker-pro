from abc import ABC, abstractmethod
from typing import Optional

class TTSBase(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
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
        cache_length: int
    ) -> bytes:
        """
        Generate speech from text.
        
        Returns:
            bytes: WAV audio data
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the TTS engine is available"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources (models, etc.)"""
        pass