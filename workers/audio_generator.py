"""
Worker thread for generating a single audio clip from text.
"""

from PySide6.QtCore import QThread, Signal
from core.tts_base import TTSBase


class AudioGeneratorWorker(QThread):
    """
    Worker thread for generating audio from text.
    Runs TTS generation in background to keep UI responsive.
    """
    
    # Signals
    finished = Signal(bytes)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, tts_engine: TTSBase, text: str, settings: dict):
        """
        Initialize the worker.
        
        Args:
            tts_engine: Instance of TTSBase (local or API)
            text: Text to convert to speech
            settings: Dictionary of TTS settings
        """
        super().__init__()
        self.tts_engine = tts_engine
        self.text = text
        self.settings = settings
    
    def run(self):
        """Execute the audio generation task"""
        try:
            self.progress.emit("Generating audio...")
            
            # Filter out any engine config that might have slipped through
            tts_params = {k: v for k, v in self.settings.items() 
                         if k not in ['engine_type', 'api_url']}
            
            audio_data = self.tts_engine.generate_speech(
                text=self.text,
                **tts_params
            )
            
            self.progress.emit("Audio generated successfully!")
            self.finished.emit(audio_data)
            
        except Exception as e:
            import traceback
            print("=" * 60)
            print("ERROR in AudioGeneratorWorker:")
            print(traceback.format_exc())
            print("=" * 60)
            self.error.emit(str(e))