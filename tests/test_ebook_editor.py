"""
Unit tests for ebook editor functionality.
"""

import pytest
import os
import tempfile
from pathlib import Path

from ebook_editor.core.models import Book, Chapter
from ebook_editor.core.services import EbookService
from ebook_editor.utils.html_clean import sanitize_html
from ebook_editor.utils.splitters import ChapterSplitter


class TestHtmlCleaning:
    """Test HTML sanitization."""
    
    def test_normalize_tags(self):
        """Test tag normalization."""
        html = "<strong>Bold</strong> <em>Italic</em>"
        result = sanitize_html(html)
        assert "<b>Bold</b>" in result
        assert "<i>Italic</i>" in result
    
    def test_remove_styles(self):
        """Test style attribute removal."""
        html = '<p style="color: red;">Text</p>'
        result = sanitize_html(html)
        assert 'style' not in result
        assert '<p>Text</p>' in result
    
    def test_image_alt_text(self):
        """Test image to alt text conversion."""
        html = '<p>Before <img src="pic.jpg" alt="My Image"/> After</p>'
        result = sanitize_html(html)
        assert '[Image: My Image]' in result
        assert '<img' not in result
    
    def test_strip_unknown_tags(self):
        """Test unknown tag removal."""
        html = '<div><custom>Text</custom></div>'
        result = sanitize_html(html)
        assert '<custom' not in result
        assert 'Text' in result


class TestChapterSplitter:
    """Test chapter splitting."""
    
    def test_chapter_number_split(self):
        """Test splitting by chapter numbers."""
        text = "Chapter 1\nContent 1\n\nChapter 2\nContent 2"
        chapters = ChapterSplitter.split_text(text, 'chapter_number')
        
        assert len(chapters) >= 2
        assert any('Chapter 1' in title for title, _ in chapters)
    
    def test_no_chapters_detected(self):
        """Test when no chapters detected."""
        text = "Just some plain text without chapter markers"
        chapters = ChapterSplitter.split_text(text, 'chapter_number')
        
        assert len(chapters) == 1
        assert chapters[0][0] == "Chapter 1"


class TestBookModel:
    """Test Book and Chapter models."""
    
    def test_create_book(self):
        """Test book creation."""
        book = Book(title="Test Book", author="Test Author")
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert len(book.chapters) == 0
        assert not book.is_dirty
    
    def test_add_chapter(self):
        """Test adding chapters."""
        book = Book(title="Test")
        chapter = Chapter(id="ch1", title="Chapter 1", html="<p>Content</p>", order=0)
        
        book.add_chapter(chapter)
        
        assert len(book.chapters) == 1
        assert book.is_dirty
    
    def test_move_chapter(self):
        """Test chapter reordering."""
        book = Book(title="Test")
        ch1 = Chapter(id="ch1", title="Ch1", html="<p>1</p>", order=0)
        ch2 = Chapter(id="ch2", title="Ch2", html="<p>2</p>", order=1)
        
        book.add_chapter(ch1)
        book.add_chapter(ch2)
        book.mark_clean()
        
        book.move_chapter(0, 1)
        
        assert book.chapters[0].id == "ch2"
        assert book.chapters[1].id == "ch1"
        assert book.is_dirty


class TestEpubExportImport:
    """Test EPUB export and import."""
    
    def test_export_single_chapter(self):
        """Test exporting a single chapter."""
        book = Book(title="Test Book", author="Test Author")
        chapter = Chapter(id="ch1", title="Test Chapter", html="<p>Test content</p>", order=0)
        book.add_chapter(chapter)
        
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            service = EbookService()
            service.export_chapter(book, "ch1", tmp_path)
            
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
            
            # Re-import and verify
            imported_book = service.open_ebook(tmp_path)
            assert len(imported_book.chapters) == 1
            assert imported_book.chapters[0].title == "Test Chapter"
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_export_full_book(self):
        """Test exporting a full book."""
        book = Book(title="Test Book", author="Test Author")
        book.add_chapter(Chapter(id="ch1", title="Ch1", html="<p>Content 1</p>", order=0))
        book.add_chapter(Chapter(id="ch2", title="Ch2", html="<p>Content 2</p>", order=1))
        
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            service = EbookService()
            service.save_as_epub(book, tmp_path)
            
            assert os.path.exists(tmp_path)
            
            # Re-import and verify
            imported_book = service.open_ebook(tmp_path)
            assert len(imported_book.chapters) == 2
            assert imported_book.title == "Test Book"
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestTxtImport:
    """Test TXT file import."""
    
    def test_import_txt_with_chapters(self):
        """Test importing TXT with chapter markers."""
        content = "Chapter 1\nFirst chapter content\n\nChapter 2\nSecond chapter content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            service = EbookService()
            book = service.open_ebook(tmp_path)
            
            assert len(book.chapters) >= 2
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()