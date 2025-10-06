"""
PDF file importer with text extraction and chapter splitting.
"""

import fitz  # PyMuPDF
from typing import List
from ..core.models import Book, Chapter
from ..utils.splitters import ChapterSplitter
from ..utils.html_clean import wrap_in_paragraphs
import os


class PdfImporter:
    """Import PDF files with text extraction."""
    
    @staticmethod
    def import_file(filepath: str, heuristic: str = 'chapter_number') -> Book:
        """
        Import a PDF file.
        
        Args:
            filepath: Path to PDF file
            heuristic: Chapter splitting heuristic
            
        Returns:
            Book object
        """
        # Open PDF
        doc = fitz.open(filepath)
        
        # Extract all text
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()
        
        doc.close()
        
        # Extract metadata
        filename = os.path.basename(filepath)
        title = os.path.splitext(filename)[0]
        
        # Try to get PDF metadata
        doc = fitz.open(filepath)
        metadata = doc.metadata
        if metadata.get('title'):
            title = metadata['title']
        author = metadata.get('author', 'Unknown Author')
        doc.close()
        
        # Split into chapters
        chapter_data = ChapterSplitter.split_text(full_text, heuristic)
        
        # Create chapters
        chapters = []
        for i, (chapter_title, content) in enumerate(chapter_data):
            html = wrap_in_paragraphs(content)
            
            chapter = Chapter(
                id=f"ch_{i+1}",
                title=chapter_title,
                html=html,
                order=i
            )
            chapters.append(chapter)
        
        # Create book
        book = Book(
            title=title,
            author=author,
            chapters=chapters,
            source_path=filepath
        )
        
        return book