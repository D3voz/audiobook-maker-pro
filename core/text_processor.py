# text_processor.py
import re
from typing import List, Tuple
import os

class TextProcessor:
    """Handles text extraction from various formats and intelligent chunking"""
    
    def __init__(self, max_chunk_size: int = 4000):
        """
        Initialize the text processor.
        
        Args:
            max_chunk_size: Maximum characters per chunk (leaving buffer from 4096 limit)
        """
        self.max_chunk_size = max_chunk_size
    
    def load_text_from_file(self, filepath: str) -> str:
        """
        Load text from various file formats.
        
        Args:
            filepath: Path to the file
            
        Returns:
            str: Extracted text
            
        Raises:
            Exception: If file format is not supported or reading fails
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.txt':
            return self._load_txt(filepath)
        elif ext == '.pdf':
            return self._load_pdf(filepath)
        elif ext == '.epub':
            return self._load_epub(filepath)
        else:
            raise Exception(f"Unsupported file format: {ext}")
    
    def _load_txt(self, filepath: str) -> str:
        """Load text from a .txt file"""
        try:
            # Try UTF-8 first
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _load_pdf(self, filepath: str) -> str:
        """Load text from a .pdf file"""
        try:
            import PyPDF2
            text = []
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n\n'.join(text)
        except ImportError:
            raise Exception("PyPDF2 is required for PDF support. Install it with: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def _load_epub(self, filepath: str) -> str:
        """Load text from an .epub file"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book = epub.read_epub(filepath)
            text = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text.append(soup.get_text())
            
            return '\n\n'.join(text)
        except ImportError:
            raise Exception("ebooklib and beautifulsoup4 are required for EPUB support. "
                          "Install them with: pip install ebooklib beautifulsoup4")
        except Exception as e:
            raise Exception(f"Error reading EPUB: {str(e)}")
    
    def chunk_text(self, text: str, respect_paragraphs: bool = True) -> List[str]:
        """
        Split text into chunks that fit within the API limit.
        
        Args:
            text: The text to split
            respect_paragraphs: If True, try to split at paragraph boundaries
            
        Returns:
            List of text chunks
        """
        # Clean up the text
        text = self._clean_text(text)
        
        if len(text) <= self.max_chunk_size:
            return [text]
        
        if respect_paragraphs:
            return self._chunk_by_paragraphs(text)
        else:
            return self._chunk_by_sentences(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean up text by removing excessive whitespace"""
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        # Remove spaces at start/end of lines
        text = '\n'.join(line.strip() for line in text.split('\n'))
        return text.strip()
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs, combining small ones"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para)
            
            # If single paragraph is too long, split it by sentences
            if para_length > self.max_chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split the long paragraph
                sentence_chunks = self._chunk_by_sentences(para)
                chunks.extend(sentence_chunks)
                continue
            
            # If adding this paragraph would exceed limit, save current chunk
            if current_length + para_length + 2 > self.max_chunk_size:  # +2 for \n\n
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length + 2
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences"""
        # Simple sentence splitting (can be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence)
            
            # If single sentence is too long, force split it
            if sentence_length > self.max_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Force split by words
                words = sentence.split()
                word_chunk = []
                word_length = 0
                
                for word in words:
                    if word_length + len(word) + 1 > self.max_chunk_size:
                        chunks.append(' '.join(word_chunk))
                        word_chunk = [word]
                        word_length = len(word)
                    else:
                        word_chunk.append(word)
                        word_length += len(word) + 1
                
                if word_chunk:
                    chunks.append(' '.join(word_chunk))
                continue
            
            if current_length + sentence_length + 1 > self.max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def estimate_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Estimate the audio duration in minutes.
        
        Args:
            text: The text to estimate
            words_per_minute: Average speaking speed
            
        Returns:
            Estimated duration in minutes
        """
        word_count = len(text.split())
        return word_count / words_per_minute