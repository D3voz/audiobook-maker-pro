"""
HTML sanitization and normalization utilities.
"""

from bs4 import BeautifulSoup, NavigableString, Tag
import re


# Allowed tags and attributes per specification
ALLOWED_TAGS = {
    'p', 'br', 'h1', 'h2', 'h3', 'b', 'i', 'u', 
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 
    'a', 'hr', 'sup', 'sub'
}

ALLOWED_ATTRIBUTES = {
    'a': ['href']
}

# Tag normalizations
TAG_NORMALIZATIONS = {
    'strong': 'b',
    'em': 'i',
    'h4': 'h3',
    'h5': 'h3',
    'h6': 'h3',
    'div': 'p'
}


def strip_css_artifacts(text: str) -> str:
    """
    Remove CSS artifacts that might appear as text.
    
    Args:
        text: Text that might contain CSS
        
    Returns:
        Cleaned text
    """
    # Remove common CSS patterns
    patterns = [
        r'p,\s*li\s*\{[^}]+\}',
        r'hr\s*\{[^}]+\}',
        r'li\.(un)?checked::[^{]+\{[^}]+\}',
        r'@page\s*\{[^}]+\}',
        r'@media[^{]+\{[^}]+\}',
        r'\*\s*\{[^}]+\}',
        r'body\s*\{[^}]+\}',
        r'white-space:\s*pre-wrap;',
        r'border-width:\s*\d+;',
        r'content:\s*"[^"]+";',
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove multiple spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    
    return cleaned.strip()


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML according to the allowlist.
    
    - Preserve minimal, safe formatting
    - Normalize tags (strong→b, em→i, etc.)
    - Strip images, append alt text
    - Remove all disallowed attributes, styles, classes, ids
    - Validate href attributes (only http/https/mailto)
    - Remove <style>, <script>, <meta> tags completely
    
    Args:
        html: Raw HTML string
        
    Returns:
        Sanitized HTML string
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted tags completely (including their content)
    for tag in soup.find_all(['style', 'script', 'meta', 'link', 'head']):
        tag.decompose()
    
    # Process all remaining tags
    for tag in soup.find_all(True):
        _process_tag(tag)
    
    # Get clean HTML
    result = str(soup)
    
    # Clean up excessive whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Strip any CSS artifacts that leaked through
    result = strip_css_artifacts(result)
    
    return result.strip()


def _process_tag(tag: Tag):
    """Process a single tag for sanitization."""
    
    # Handle images - convert to text
    if tag.name == 'img':
        alt_text = tag.get('alt', '')
        if alt_text:
            text_node = NavigableString(f" [Image: {alt_text}] ")
            tag.replace_with(text_node)
        else:
            tag.decompose()
        return
    
    # Normalize tag names
    if tag.name in TAG_NORMALIZATIONS:
        tag.name = TAG_NORMALIZATIONS[tag.name]
    
    # Remove disallowed tags but keep their content
    if tag.name not in ALLOWED_TAGS:
        tag.unwrap()
        return
    
    # Clean attributes
    allowed_attrs = ALLOWED_ATTRIBUTES.get(tag.name, [])
    attrs_to_remove = []
    
    for attr in tag.attrs:
        if attr not in allowed_attrs:
            attrs_to_remove.append(attr)
    
    for attr in attrs_to_remove:
        del tag[attr]
    
    # Validate href attributes
    if tag.name == 'a' and 'href' in tag.attrs:
        href = tag['href']
        if not _is_valid_href(href):
            del tag['href']
            tag.unwrap()  # Remove link if href is invalid


def _is_valid_href(href: str) -> bool:
    """Validate href attribute - only http/https/mailto."""
    if not href:
        return False
    
    href_lower = href.lower().strip()
    return (
        href_lower.startswith('http://') or
        href_lower.startswith('https://') or
        href_lower.startswith('mailto:')
    )


def html_to_plain_text(html: str) -> str:
    """Convert HTML to plain text (for previews)."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove style and script tags first
    for tag in soup.find_all(['style', 'script']):
        tag.decompose()
    
    return soup.get_text(separator=' ', strip=True)


def wrap_in_paragraphs(text: str) -> str:
    """Wrap plain text in paragraph tags."""
    lines = text.split('\n\n')
    paragraphs = [f"<p>{line.strip()}</p>" for line in lines if line.strip()]
    return '\n'.join(paragraphs)