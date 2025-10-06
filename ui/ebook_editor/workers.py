"""
Worker threads for I/O operations.
"""

from PySide6.QtCore import QThread, Signal

from ebook_editor.core.models import Book
from ebook_editor.core.services import EbookService


class OpenBookWorker(QThread):
    """Worker for opening books."""
    
    finished = Signal(Book)
    error = Signal(str)
    
    def __init__(self, service: EbookService, filepath: str, heuristic: str = 'chapter_number'):
        super().__init__()
        self.service = service
        self.filepath = filepath
        self.heuristic = heuristic
    
    def run(self):
        """Open the book."""
        try:
            book = self.service.open_ebook(self.filepath, self.heuristic)
            self.finished.emit(book)
        except Exception as e:
            self.error.emit(str(e))


class SaveBookWorker(QThread):
    """Worker for saving books."""
    
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, service: EbookService, book: Book, filepath: str):
        super().__init__()
        self.service = service
        self.book = book
        self.filepath = filepath
    
    def run(self):
        """Save the book."""
        try:
            self.service.save_as_epub(self.book, self.filepath)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ExportChapterWorker(QThread):
    """Worker for exporting chapters."""
    
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, service: EbookService, book: Book, chapter_id: str, filepath: str):
        super().__init__()
        self.service = service
        self.book = book
        self.chapter_id = chapter_id
        self.filepath = filepath
    
    def run(self):
        """Export the chapter."""
        try:
            self.service.export_chapter(self.book, self.chapter_id, self.filepath)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))