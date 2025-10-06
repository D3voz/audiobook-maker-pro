"""
Heuristic-based chapter splitting for PDF and TXT files.
"""

import re
from typing import List, Tuple, Pattern


class ChapterSplitter:
    """Heuristic-based chapter splitting."""
    
    # Predefined heuristics
    HEURISTICS = {
        'chapter_number': (
            r'^\s*(chapter|ch\.?)\s+\d+\b',
            'Chapter/Ch. followed by number'
        ),
        'part_section': (
            r'^\s*(part|section)\s+\d+\b',
            'Part/Section followed by number'
        ),
        'markdown_heading': (
            r'^#{1,3}\s+.+$',
            'Markdown-style headings (# ## ###)'
        ),
        'all_caps_heading': (
            r'^\s*[A-Z][A-Z\s]{10,}$',
            'ALL CAPS HEADINGS (min 10 chars)'
        )
    }
    
    @staticmethod
    def split_text(text: str, heuristic_name: str = 'chapter_number') -> List[Tuple[str, str]]:
        """
        Split text into chapters using a heuristic.
        
        Args:
            text: Full text content
            heuristic_name: Name of heuristic to use
            
        Returns:
            List of (title, content) tuples
        """
        if heuristic_name not in ChapterSplitter.HEURISTICS:
            heuristic_name = 'chapter_number'
        
        pattern_str, _ = ChapterSplitter.HEURISTICS[heuristic_name]
        pattern = re.compile(pattern_str, re.MULTILINE | re.IGNORECASE)
        
        # Find all matches
        matches = list(pattern.finditer(text))
        
        if not matches:
            # No chapters detected - return as single chapter
            return [("Chapter 1", text)]
        
        chapters = []
        
        for i, match in enumerate(matches):
            # Extract title from the matched line
            title_line = text[match.start():text.find('\n', match.start())]
            title = title_line.strip()
            
            # Clean up title
            title = re.sub(r'^#+\s*', '', title)  # Remove markdown #
            title = title.strip()
            
            if not title:
                title = f"Chapter {i + 1}"
            
            # Extract content
            content_start = match.end()
            content_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[content_start:content_end].strip()
            
            chapters.append((title, content))
        
        return chapters
    
    @staticmethod
    def preview_split(text: str, heuristic_name: str) -> List[dict]:
        """
        Preview chapter split without creating full chapters.
        
        Args:
            text: Full text content
            heuristic_name: Name of heuristic to use
            
        Returns:
            List of preview dicts with title and preview text
        """
        chapters = ChapterSplitter.split_text(text, heuristic_name)
        
        previews = []
        for title, content in chapters:
            preview_text = content[:200] + "..." if len(content) > 200 else content
            previews.append({
                'title': title,
                'preview': preview_text,
                'length': len(content)
            })
        
        return previews