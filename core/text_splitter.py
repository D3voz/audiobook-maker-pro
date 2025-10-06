"""
Advanced text splitting functions adapted from tts-webui.
Handles intelligent text chunking for optimal TTS generation.
"""

import re
from typing import List


def split_and_recombine_text(
    text: str,
    desired_length: int = 200,
    max_length: int = 300
) -> List[str]:
    """
    Split text into chunks while respecting sentence boundaries.
    Adapted from tts-webui's split_text_functions.
    
    Args:
        text: Text to split
        desired_length: Target length for each chunk
        max_length: Maximum allowed chunk length
        
    Returns:
        List of text chunks
    """
    # Normalize text
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split into sentences
    sentences = _split_into_sentences(text)
    
    if not sentences:
        return [text] if text.strip() else []
    
    # Combine sentences into chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If single sentence exceeds max_length, split it further
        if sentence_length > max_length:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Split long sentence
            sub_chunks = _split_long_sentence(sentence, max_length)
            chunks.extend(sub_chunks)
            continue
        
        # Check if adding this sentence would exceed desired_length
        if current_length + sentence_length > desired_length and current_chunk:
            # Check if we should force-add (if we haven't reached max_length)
            if current_length + sentence_length <= max_length:
                # Close to desired length, add it anyway
                current_chunk.append(sentence)
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            else:
                # Save current chunk and start new one
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
        else:
            # Add to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex.
    Handles common abbreviations and edge cases.
    """
    # Common abbreviations that shouldn't trigger sentence breaks
    abbreviations = {
        'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.',
        'vs.', 'etc.', 'i.e.', 'e.g.', 'al.', 'Ph.D.'
    }
    
    # Temporarily replace abbreviations
    protected_text = text
    replacements = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        protected_text = protected_text.replace(abbr, placeholder)
        replacements[placeholder] = abbr
    
    # Split on sentence endings
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(pattern, protected_text)
    
    # Restore abbreviations
    restored_sentences = []
    for sentence in sentences:
        for placeholder, abbr in replacements.items():
            sentence = sentence.replace(placeholder, abbr)
        
        sentence = sentence.strip()
        if sentence:
            restored_sentences.append(sentence)
    
    return restored_sentences


def _split_long_sentence(sentence: str, max_length: int) -> List[str]:
    """
    Split a very long sentence into smaller chunks.
    Tries to split at natural boundaries (commas, semicolons, etc.)
    """
    if len(sentence) <= max_length:
        return [sentence]
    
    # Try to split at punctuation
    split_points = [',', ';', ':', ' - ', ' – ']
    
    for punct in split_points:
        if punct in sentence:
            parts = sentence.split(punct)
            
            chunks = []
            current = ""
            
            for i, part in enumerate(parts):
                # Re-add punctuation except for last part
                if i < len(parts) - 1:
                    part += punct
                
                if len(current) + len(part) <= max_length:
                    current += part
                else:
                    if current:
                        chunks.append(current.strip())
                    current = part
            
            if current:
                chunks.append(current.strip())
            
            # Check if all chunks are within limit
            if all(len(c) <= max_length for c in chunks):
                return chunks
    
    # Last resort: split at word boundaries
    words = sentence.split()
    chunks = []
    current = ""
    
    for word in words:
        if len(current) + len(word) + 1 <= max_length:
            current += word + " "
        else:
            if current:
                chunks.append(current.strip())
            current = word + " "
    
    if current:
        chunks.append(current.strip())
    
    return chunks


def estimate_duration(text: str, words_per_minute: int = 150) -> float:
    """
    Estimate audio duration in minutes.
    
    Args:
        text: Text to estimate
        words_per_minute: Average speaking rate (default 150 WPM)
        
    Returns:
        Estimated duration in minutes
    """
    word_count = len(text.split())
    return word_count / words_per_minute