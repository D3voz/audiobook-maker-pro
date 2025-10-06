"""
EPUB exporter for single chapters and full books.
"""

from ebooklib import epub
from ..core.models import Book, Chapter
from typing import Optional


class EpubExporter:
    """Export books and chapters as EPUB files."""
    
    @staticmethod
    def export_chapter(book: Book, chapter: Chapter, output_path: str):
        """
        Export a single chapter as a standalone EPUB.
        
        Args:
            book: Source book (for metadata)
            chapter: Chapter to export
            output_path: Output file path
        """
        # Create EPUB book
        epub_book = epub.EpubBook()
        
        # Set metadata
        chapter_title = f"{book.title} - {chapter.title}"
        epub_book.set_identifier(f"{book.identifier}_ch{chapter.id}")
        epub_book.set_title(chapter_title)
        epub_book.set_language(book.language)
        epub_book.add_author(book.author)
        
        # Create chapter item
        epub_chapter = epub.EpubHtml(
            title=chapter.title,
            file_name=f'{chapter.id}.xhtml',
            lang=book.language
        )
        epub_chapter.content = f'<html><head><title>{chapter.title}</title></head><body>{chapter.html}</body></html>'
        
        # Add chapter
        epub_book.add_item(epub_chapter)
        
        # Define spine
        epub_book.spine = ['nav', epub_chapter]
        
        # Add navigation
        epub_book.toc = (epub_chapter,)
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())
        
        # Write EPUB
        epub.write_epub(output_path, epub_book)
    
    @staticmethod
    def export_book(book: Book, output_path: str):
        """
        Export full book as EPUB.
        
        Args:
            book: Book to export
            output_path: Output file path
        """
        # Create EPUB book
        epub_book = epub.EpubBook()
        
        # Set metadata
        epub_book.set_identifier(book.identifier)
        epub_book.set_title(book.title)
        epub_book.set_language(book.language)
        epub_book.add_author(book.author)
        
        # Add chapters in order
        epub_chapters = []
        toc = []
        
        for chapter in sorted(book.chapters, key=lambda c: c.order):
            epub_chapter = epub.EpubHtml(
                title=chapter.title,
                file_name=f'{chapter.id}.xhtml',
                lang=book.language
            )
            epub_chapter.content = f'<html><head><title>{chapter.title}</title></head><body>{chapter.html}</body></html>'
            
            epub_book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            toc.append(epub_chapter)
        
        # Define spine (reading order)
        epub_book.spine = ['nav'] + epub_chapters
        
        # Add navigation
        epub_book.toc = tuple(toc)
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())
        
        # Write EPUB
        epub.write_epub(output_path, epub_book)