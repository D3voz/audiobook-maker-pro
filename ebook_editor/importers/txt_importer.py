"""
TXT file importer with encoding detection and chapter splitting.
"""

import chardet
from typing import List
from ..core.models import Book, Chapter
from ..utils.splitters import ChapterSplitter
from ..utils.html_clean import wrap_in_paragraphs
import os


class TxtImporter:
    """Import TXT files with encoding detection."""
    
    @staticmethod
    def import_file(filepath: str, heuristic: str = 'chapter_number') -> Book:
        """
        Import a TXT file.
        
        Args:
            filepath: Path to TXT file
            heuristic: Chapter splitting heuristic
            
        Returns:
            Book object
        """
        # Detect encoding
        with open(filepath, 'rb') as f:
            raw_data = f.read()
        
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] or 'utf-8'
        
        # Read text with detected encoding
        try:
            text = raw_data.decode(encoding)
        except:
            # Fallback to utf-8 with error replacement
            text = raw_data.decode('utf-8', errors='replace')
        
        # Extract metadata from filename
        filename = os.path.basename(filepath)
        title = os.path.splitext(filename)[0]
        
        # Split into chapters
        chapter_data = ChapterSplitter.split_text(text, heuristic)
        
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
            author="Unknown Author",
            chapters=chapters,
            source_path=filepath
        )
        
        return book