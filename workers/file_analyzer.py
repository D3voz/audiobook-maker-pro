"""
Worker thread for analyzing text files.
"""

from PySide6.QtCore import QThread, Signal
from core.audiobook_maker import AudiobookMaker


class FileAnalyzerWorker(QThread):
    """
    Worker thread for analyzing text files.
    Extracts file information without blocking the UI.
    """
    
    # Signals
    finished = Signal(dict)  # Emits file info dictionary
    error = Signal(str)      # Emits error message
    
    def __init__(self, audiobook_maker: AudiobookMaker, filepath: str):
        """
        Initialize the worker.
        
        Args:
            audiobook_maker: Instance of AudiobookMaker
            filepath: Path to the file to analyze
        """
        super().__init__()
        self.audiobook_maker = audiobook_maker
        self.filepath = filepath
    
    def run(self):
        """Execute the file analysis task"""
        try:
            info = self.audiobook_maker.get_text_info(self.filepath)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))