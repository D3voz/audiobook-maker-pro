import io
import wave
import numpy as np
from typing import Callable, Optional, List
import scipy.io.wavfile as wavfile
from .text_processor import TextProcessor
from .tts_base import TTSBase  # Changed from TTSClient


class AudiobookMaker:
    """Handles the creation of audiobooks from text"""
    
    def __init__(self, tts_engine: TTSBase):  # Changed parameter name
        """
        Initialize the audiobook maker.
        
        Args:
            tts_engine: Instance of TTSBase (local or API)
        """
        self.tts_engine = tts_engine  # Changed from tts_client
        self.text_processor = TextProcessor(max_chunk_size=4000)
        self.cancel_requested = False
    
    def cancel(self):
        """Request cancellation of current audiobook generation"""
        self.cancel_requested = True
    
    def create_audiobook(
        self,
        text: str,
        output_path: str,
        tts_settings: dict,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """
        Create an audiobook from text.
        (Rest of implementation stays the same)
        """
        self.cancel_requested = False
        
        chunks = self.text_processor.chunk_text(text, respect_paragraphs=True)
        total_chunks = len(chunks)
        
        if progress_callback:
            progress_callback(0, total_chunks, f"Split text into {total_chunks} chunks")
        
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            if self.cancel_requested:
                if progress_callback:
                    progress_callback(i, total_chunks, "Cancelled by user")
                return False
            
            if progress_callback:
                progress_callback(i, total_chunks, f"Generating chunk {i+1}/{total_chunks}")
            
            try:
                audio_data = self.tts_engine.generate_speech(  # Changed from tts_client
                    text=chunk,
                    **tts_settings
                )
                audio_segments.append(audio_data)
                
            except Exception as e:
                raise Exception(f"Error generating chunk {i+1}/{total_chunks}: {str(e)}")
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Combining audio segments...")
        
        combined_audio = self._combine_audio_segments(audio_segments)
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Saving audiobook...")
        
        with open(output_path, 'wb') as f:
            f.write(combined_audio)
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Complete!")
        
        return True
    
    def create_audiobook_from_file(
        self,
        filepath: str,
        output_path: str,
        tts_settings: dict,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """Create an audiobook from a file."""
        if progress_callback:
            progress_callback(0, 1, "Loading text from file...")
        
        text = self.text_processor.load_text_from_file(filepath)
        
        return self.create_audiobook(text, output_path, tts_settings, progress_callback)
    
    def _combine_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """Combine multiple WAV audio segments into one."""
        if not audio_segments:
            raise Exception("No audio segments to combine")
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        combined_data = []
        sample_rate = None
        
        for segment in audio_segments:
            rate, data = wavfile.read(io.BytesIO(segment))
            
            if sample_rate is None:
                sample_rate = rate
            elif sample_rate != rate:
                raise Exception(f"Sample rate mismatch: {sample_rate} vs {rate}")
            
            combined_data.append(data)
        
        final_audio = np.concatenate(combined_data)
        
        output_buffer = io.BytesIO()
        wavfile.write(output_buffer, sample_rate, final_audio)
        
        return output_buffer.getvalue()
    
    def get_text_info(self, filepath: str) -> dict:
        """Get information about a text file without processing it."""
        text = self.text_processor.load_text_from_file(filepath)
        chunks = self.text_processor.chunk_text(text)
        
        return {
            'total_characters': len(text),
            'total_words': len(text.split()),
            'total_chunks': len(chunks),
            'estimated_duration_minutes': self.text_processor.estimate_duration(text),
            'preview': text[:500] + '...' if len(text) > 500 else text
        }
    
    def cleanup(self):
        """Cleanup TTS engine resources"""
        if hasattr(self, 'tts_engine'):
            self.tts_engine.cleanup()