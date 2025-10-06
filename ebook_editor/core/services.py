"""
Core services for ebook operations.
"""

import os
from typing import Optional
from .models import Book, Chapter
from ..importers.epub_importer import EpubImporter
from ..importers.pdf_importer import PdfImporter
from ..importers.txt_importer import TxtImporter
from ..exporters.epub_exporter import EpubExporter


class EbookService:
    """
    Service layer for ebook operations.
    Coordinates importers, exporters, and business logic.
    """
    
    @staticmethod
    def open_ebook(filepath: str, heuristic: str = 'chapter_number') -> Book:
        """
        Open an ebook file.
        
        Args:
            filepath: Path to ebook file
            heuristic: Splitting heuristic for PDF/TXT
            
        Returns:
            Book object
            
        Raises:
            ValueError: If file format not supported
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.epub':
            return EpubImporter.import_file(filepath)
        elif ext == '.pdf':
            return PdfImporter.import_file(filepath, heuristic)
        elif ext == '.txt':
            return TxtImporter.import_file(filepath, heuristic)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    @staticmethod
    def save_as_epub(book: Book, output_path: str):
        """
        Save book as EPUB.
        
        Args:
            book: Book to save
            output_path: Output file path
        """
        EpubExporter.export_book(book, output_path)
        book.mark_clean()
        book.source_path = output_path
    
    @staticmethod
    def export_chapter(book: Book, chapter_id: str, output_path: str):
        """
        Export a single chapter as EPUB.
        
        Args:
            book: Source book
            chapter_id: ID of chapter to export
            output_path: Output file path
            
        Raises:
            ValueError: If chapter not found
        """
        chapter = book.get_chapter_by_id(chapter_id)
        if not chapter:
            raise ValueError(f"Chapter not found: {chapter_id}")
        
        EpubExporter.export_chapter(book, chapter, output_path)
    
    @staticmethod
    def import_chapter(book: Book, epub_path: str):
        """
        Import a chapter from a single-chapter EPUB.
        
        Args:
            book: Target book
            epub_path: Path to single-chapter EPUB
            
        Raises:
            ValueError: If EPUB has multiple chapters
        """
        # Validate single chapter
        if not EpubImporter.validate_single_chapter(epub_path):
            raise ValueError(
                "Import failed: EPUB must contain exactly one chapter.\n"
                "Multi-chapter EPUBs are not supported for import."
            )
        
        # Import the chapter
        temp_book = EpubImporter.import_file(epub_path)
        
        if not temp_book.chapters:
            raise ValueError("No chapters found in EPUB")
        
        # Get the single chapter
        imported_chapter = temp_book.chapters[0]
        
        # Generate new ID
        new_id = f"ch_{len(book.chapters) + 1}"
        imported_chapter.id = new_id
        
        # Add to book
        book.add_chapter(imported_chapter)
    
    @staticmethod
    def create_new_book(title: str, author: str = "Unknown Author") -> Book:
        """
        Create a new empty book.
        
        Args:
            title: Book title
            author: Book author
            
        Returns:
            New Book object
        """
        return Book(title=title, author=author)
    
    @staticmethod
    def resplit_text_book(book: Book, heuristic: str) -> Book:
        """
        Re-split a text-based book with a different heuristic.
        
        Args:
            book: Current book
            heuristic: New heuristic to apply
            
        Returns:
            New Book object with re-split chapters
        """
        if not book.source_path:
            raise ValueError("Cannot re-split: no source file")
        
        ext = os.path.splitext(book.source_path)[1].lower()
        
        if ext == '.txt':
            return TxtImporter.import_file(book.source_path, heuristic)
        elif ext == '.pdf':
            return PdfImporter.import_file(book.source_path, heuristic)
        else:
            raise ValueError("Re-split only supported for TXT and PDF files")