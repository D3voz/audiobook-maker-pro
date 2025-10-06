"""
EPUB file importer using ebooklib.
"""

from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from typing import List
from ..core.models import Book, Chapter
from ..utils.html_clean import sanitize_html
import os


class EpubImporter:
    """Import EPUB files."""
    
    @staticmethod
    def import_file(filepath: str) -> Book:
        """
        Import an EPUB file.
        
        Args:
            filepath: Path to EPUB file
            
        Returns:
            Book object
        """
        # Read EPUB
        book_epub = epub.read_epub(filepath)
        
        # Extract metadata
        title = book_epub.get_metadata('DC', 'title')
        title = title[0][0] if title else os.path.splitext(os.path.basename(filepath))[0]
        
        author = book_epub.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Unknown Author"
        
        language = book_epub.get_metadata('DC', 'language')
        language = language[0][0] if language else "en"
        
        # Extract chapters in spine order
        chapters = []
        spine_ids = [item[0] for item in book_epub.spine]
        
        for i, spine_id in enumerate(spine_ids):
            item = book_epub.get_item_with_id(spine_id)
            
            if item and item.get_type() == ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8')
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # IMPORTANT: Remove style and script tags BEFORE extracting content
                for unwanted in soup.find_all(['style', 'script', 'meta', 'link']):
                    unwanted.decompose()
                
                # Extract title from HTML
                chapter_title = None
                
                # Try to get title from <title> tag
                if soup.title and soup.title.string:
                    chapter_title = soup.title.string.strip()
                
                # Fallback to first heading
                if not chapter_title:
                    for heading in soup.find_all(['h1', 'h2', 'h3']):
                        if heading.get_text(strip=True):
                            chapter_title = heading.get_text(strip=True)
                            break
                
                # Final fallback
                if not chapter_title:
                    chapter_title = f"Chapter {i + 1}"
                
                # Get body content (or entire soup if no body)
                body = soup.body if soup.body else soup
                
                # Remove any remaining style/script tags from body
                for unwanted in body.find_all(['style', 'script']):
                    unwanted.decompose()
                
                html_content = str(body)
                
                # Sanitize HTML (this will do additional cleanup)
                clean_html = sanitize_html(html_content)
                
                # Only add chapter if it has actual content
                # (some EPUBs have empty spine items for covers, etc.)
                if clean_html and len(clean_html.strip()) > 0:
                    chapter = Chapter(
                        id=f"ch_{len(chapters)+1}",
                        title=chapter_title.strip(),
                        html=clean_html,
                        order=len(chapters)
                    )
                    chapters.append(chapter)
        
        # Create book
        book = Book(
            title=title,
            author=author,
            language=language,
            chapters=chapters,
            source_path=filepath
        )
        
        return book
    
    @staticmethod
    def validate_single_chapter(filepath: str) -> bool:
        """
        Validate that an EPUB has exactly one chapter.
        Used for Import Chapter feature.
        
        Args:
            filepath: Path to EPUB file
            
        Returns:
            True if single chapter, False otherwise
        """
        try:
            book_epub = epub.read_epub(filepath)
            spine_count = len(book_epub.spine)
            return spine_count == 1
        except:
            return False