"""
Metadata display and quick edit panel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGroupBox
)
from PySide6.QtCore import Signal

from ebook_editor.core.models import Book


class MetadataPanel(QWidget):
    """
    Panel for displaying and editing book metadata.
    """
    
    # Signals
    metadata_changed = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.book = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("📋 Book Metadata")
        group_layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self.on_title_changed)
        title_layout.addWidget(self.title_edit)
        group_layout.addLayout(title_layout)
        
        # Author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.author_edit = QLineEdit()
        self.author_edit.textChanged.connect(self.on_author_changed)
        author_layout.addWidget(self.author_edit)
        group_layout.addLayout(author_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setMaximumHeight(120)
    
    def set_book(self, book: Book):
        """Set the book to display."""
        self.book = book
        self.refresh()
    
    def refresh(self):
        """Refresh metadata display."""
        if self.book:
            self.title_edit.blockSignals(True)
            self.author_edit.blockSignals(True)
            
            self.title_edit.setText(self.book.title)
            self.author_edit.setText(self.book.author)
            
            self.title_edit.blockSignals(False)
            self.author_edit.blockSignals(False)
            
            self.setEnabled(True)
        else:
            self.title_edit.clear()
            self.author_edit.clear()
            self.setEnabled(False)
    
    def on_title_changed(self, text: str):
        """Called when title changes."""
        if self.book:
            self.book.title = text
            self.metadata_changed.emit()
    
    def on_author_changed(self, text: str):
        """Called when author changes."""
        if self.book:
            self.book.author = text
            self.metadata_changed.emit()