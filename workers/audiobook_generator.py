"""
Worker thread for generating full audiobooks from files.
"""

from PySide6.QtCore import QThread, Signal
from core.audiobook_maker import AudiobookMaker


class AudiobookGeneratorWorker(QThread):
    """
    Worker thread for generating complete audiobooks.
    Handles chunking, generation, and combining of audio segments.
    """
    
    # Signals
    finished = Signal(bool, str)  # Emits (success, output_path)
    error = Signal(str)           # Emits error message
    progress = Signal(int, int, str)  # Emits (current, total, message)
    
    def __init__(self, audiobook_maker: AudiobookMaker, filepath: str, 
                 output_path: str, tts_settings: dict):
        """
        Initialize the worker.
        
        Args:
            audiobook_maker: Instance of AudiobookMaker
            filepath: Input file path
            output_path: Output audio file path
            tts_settings: Dictionary of TTS settings
        """
        super().__init__()
        self.audiobook_maker = audiobook_maker
        self.filepath = filepath
        self.output_path = output_path
        self.tts_settings = tts_settings
    
    def run(self):
        """Execute the audiobook generation task"""
        try:
            # Define progress callback that emits Qt signals
            def progress_callback(current, total, message):
                self.progress.emit(current, total, message)
            
            # Generate the audiobook
            success = self.audiobook_maker.create_audiobook_from_file(
                filepath=self.filepath,
                output_path=self.output_path,
                tts_settings=self.tts_settings,
                progress_callback=progress_callback
            )
            
            self.finished.emit(success, self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        """Request cancellation of the audiobook generation"""
        self.audiobook_maker.cancel()