"""
WYSIWYG chapter editor with formatting toolbar.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QToolBar, QFontComboBox,
    QComboBox, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QTextCharFormat, QTextCursor

from ebook_editor.core.models import Chapter
from ebook_editor.utils.html_clean import sanitize_html


class ChapterEditorWidget(QWidget):
    """
    WYSIWYG chapter editor with formatting toolbar.
    """
    
    # Signals
    content_changed = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.current_chapter = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.title_label = QLabel("No chapter selected")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        layout.addWidget(self.title_label)
        
        # Create editor FIRST (before toolbar that references it)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Now create toolbar (after editor exists)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Add editor to layout
        layout.addWidget(self.editor)
        
        # Character count
        self.char_count_label = QLabel("Characters: 0")
        self.char_count_label.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(self.char_count_label)
    
    def create_toolbar(self) -> QToolBar:
        """Create formatting toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Bold
        bold_action = QAction("B", self)
        bold_action.setCheckable(True)
        bold_action.setToolTip("Bold (Ctrl+B)")
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.format_text('bold'))
        toolbar.addAction(bold_action)
        self.bold_action = bold_action
        
        # Italic
        italic_action = QAction("I", self)
        italic_action.setCheckable(True)
        italic_action.setToolTip("Italic (Ctrl+I)")
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.format_text('italic'))
        toolbar.addAction(italic_action)
        self.italic_action = italic_action
        
        # Underline
        underline_action = QAction("U", self)
        underline_action.setCheckable(True)
        underline_action.setToolTip("Underline (Ctrl+U)")
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(lambda: self.format_text('underline'))
        toolbar.addAction(underline_action)
        self.underline_action = underline_action
        
        toolbar.addSeparator()
        
        # Heading level
        self.heading_combo = QComboBox()
        self.heading_combo.addItems(["Paragraph", "Heading 1", "Heading 2", "Heading 3"])
        self.heading_combo.currentIndexChanged.connect(self.apply_heading)
        toolbar.addWidget(self.heading_combo)
        
        toolbar.addSeparator()
        
        # Bullet list
        bullet_action = QAction("• List", self)
        bullet_action.setToolTip("Bullet List")
        bullet_action.triggered.connect(lambda: self.apply_list('bullet'))
        toolbar.addAction(bullet_action)
        
        # Numbered list
        numbered_action = QAction("1. List", self)
        numbered_action.setToolTip("Numbered List")
        numbered_action.triggered.connect(lambda: self.apply_list('numbered'))
        toolbar.addAction(numbered_action)
        
        toolbar.addSeparator()
        
        # Undo/Redo
        undo_action = QAction("↶ Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.editor.undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction("↷ Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.editor.redo)
        toolbar.addAction(redo_action)
        
        return toolbar
    
    def load_chapter(self, chapter: Chapter):
        """Load a chapter for editing."""
        self.save_current_chapter()  # Save previous chapter
        
        self.current_chapter = chapter
        self.title_label.setText(f"📖 {chapter.title}")
        
        # Sanitize HTML again before loading (extra safety)
        clean_html = sanitize_html(chapter.html)
        
        # Load HTML content
        self.editor.blockSignals(True)  # Prevent triggering content_changed
        self.editor.setHtml(clean_html)
        self.editor.blockSignals(False)
        
        self.update_char_count()
    
    def save_current_chapter(self):
        """Save current chapter edits."""
        if self.current_chapter:
            # Get HTML and sanitize
            html = self.editor.toHtml()
            clean_html = sanitize_html(html)
            
            # Update chapter
            self.current_chapter.html = clean_html
    
    def clear(self):
        """Clear the editor."""
        self.current_chapter = None
        self.editor.clear()
        self.title_label.setText("No chapter selected")
        self.update_char_count()
    
    def format_text(self, format_type: str):
        """Apply text formatting."""
        cursor = self.editor.textCursor()
        format = cursor.charFormat()
        
        if format_type == 'bold':
            weight = QFont.Normal if format.fontWeight() == QFont.Bold else QFont.Bold
            format.setFontWeight(weight)
        elif format_type == 'italic':
            format.setFontItalic(not format.fontItalic())
        elif format_type == 'underline':
            format.setFontUnderline(not format.fontUnderline())
        
        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)
    
    def apply_heading(self, index: int):
        """Apply heading level."""
        cursor = self.editor.textCursor()
        
        if index == 0:  # Paragraph
            cursor.clearBlockFormat()
        else:  # H1, H2, H3
            block_format = cursor.blockFormat()
            # Note: QTextEdit doesn't have true heading levels, 
            # so we just make the text larger/bold
            char_format = QTextCharFormat()
            if index == 1:  # H1
                char_format.setFontPointSize(20)
                char_format.setFontWeight(QFont.Bold)
            elif index == 2:  # H2
                char_format.setFontPointSize(16)
                char_format.setFontWeight(QFont.Bold)
            elif index == 3:  # H3
                char_format.setFontPointSize(14)
                char_format.setFontWeight(QFont.Bold)
            
            cursor.mergeBlockCharFormat(char_format)
    
    def apply_list(self, list_type: str):
        """Apply list formatting."""
        cursor = self.editor.textCursor()
        
        if list_type == 'bullet':
            self.editor.insertUnorderedList()
        elif list_type == 'numbered':
            self.editor.insertOrderedList()
    
    def on_text_changed(self):
        """Called when text changes."""
        self.update_char_count()
        self.content_changed.emit()
    
    def update_char_count(self):
        """Update character count label."""
        text = self.editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        
        self.char_count_label.setText(
            f"Characters: {char_count:,} | Words: {word_count:,}"
        )