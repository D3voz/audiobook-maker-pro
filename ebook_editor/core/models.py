"""
Core data models for the ebook editor.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Chapter:
    """Represents a single chapter in an ebook."""
    
    id: str
    title: str
    html: str  # UTF-8 HTML fragment
    order: int
    
    def __post_init__(self):
        """Validate chapter data."""
        if not self.title:
            raise ValueError("Chapter title cannot be empty")
        if not isinstance(self.html, str):
            raise ValueError("Chapter HTML must be a string")


@dataclass
class Book:
    """Represents an ebook with metadata and chapters."""
    
    title: str
    author: str = "Unknown Author"
    language: str = "en"
    identifier: str = field(default_factory=lambda: f"urn:uuid:{datetime.now().timestamp()}")
    chapters: List[Chapter] = field(default_factory=list)
    source_path: Optional[str] = None
    is_dirty: bool = False
    
    def __post_init__(self):
        """Validate book data."""
        if not self.title:
            raise ValueError("Book title cannot be empty")
    
    def get_chapter_by_id(self, chapter_id: str) -> Optional[Chapter]:
        """Get chapter by ID."""
        for chapter in self.chapters:
            if chapter.id == chapter_id:
                return chapter
        return None
    
    def get_chapter_index(self, chapter_id: str) -> int:
        """Get chapter index by ID."""
        for i, chapter in enumerate(self.chapters):
            if chapter.id == chapter_id:
                return i
        return -1
    
    def move_chapter(self, from_index: int, to_index: int):
        """Move chapter and update order."""
        if 0 <= from_index < len(self.chapters) and 0 <= to_index < len(self.chapters):
            chapter = self.chapters.pop(from_index)
            self.chapters.insert(to_index, chapter)
            
            # Update order for all chapters
            for i, ch in enumerate(self.chapters):
                ch.order = i
            
            self.is_dirty = True
    
    def add_chapter(self, chapter: Chapter):
        """Add a chapter to the book."""
        chapter.order = len(self.chapters)
        self.chapters.append(chapter)
        self.is_dirty = True
    
    def remove_chapter(self, chapter_id: str):
        """Remove a chapter by ID."""
        index = self.get_chapter_index(chapter_id)
        if index >= 0:
            self.chapters.pop(index)
            # Update order
            for i, ch in enumerate(self.chapters):
                ch.order = i
            self.is_dirty = True
    
    def mark_dirty(self):
        """Mark the book as modified."""
        self.is_dirty = True
    
    def mark_clean(self):
        """Mark the book as saved."""
        self.is_dirty = False