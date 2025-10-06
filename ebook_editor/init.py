"""
Ebook Chapter Extractor & Editor Module
Integrated into Audiobook Maker Pro
"""

from .core.models import Book, Chapter
from .core.services import EbookService

__all__ = ['Book', 'Chapter', 'EbookService']
__version__ = '1.0.0'