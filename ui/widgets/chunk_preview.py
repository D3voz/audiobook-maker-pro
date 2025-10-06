"""
Chunk preview widget to show how text will be split.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor


class ChunkPreviewWidget(QWidget):
    """
    Widget to preview text chunks before generation.
    Shows chunks with status indicators.
    """
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📋 Chunk Preview")
        header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(header)
        
        # Info label
        self.info_label = QLabel("No content to preview")
        self.info_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.info_label)
        
        # List widget
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.chunks = []
    
    def set_chunks(self, chunks: list):
        """
        Set the chunks to preview.
        
        Args:
            chunks: List of text chunks
        """
        self.chunks = chunks
        self.list_widget.clear()
        
        if not chunks:
            self.info_label.setText("No content to preview")
            return
        
        self.info_label.setText(f"Total chunks: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            # Create preview text (first 100 chars)
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            preview = preview.replace('\n', ' ')  # Single line
            
            item_text = f"Chunk {i+1}: {preview}"
            item = QListWidgetItem(item_text)
            
            # Set status color (pending)
            item.setForeground(QColor("#888888"))
            
            self.list_widget.addItem(item)
    
    def update_chunk_status(self, chunk_index: int, status: str = "processing"):
        """
        Update the status of a chunk.
        
        Args:
            chunk_index: Index of the chunk
            status: 'processing', 'completed', or 'error'
        """
        if chunk_index >= self.list_widget.count():
            return
        
        item = self.list_widget.item(chunk_index)
        
        if status == "processing":
            item.setForeground(QColor("#00ffff"))  # Cyan
            icon = "⏳"
        elif status == "completed":
            item.setForeground(QColor("#00ff00"))  # Green
            icon = "✓"
        elif status == "error":
            item.setForeground(QColor("#ff0000"))  # Red
            icon = "✗"
        else:
            item.setForeground(QColor("#888888"))  # Gray (pending)
            icon = "○"
        
        # Update text with icon
        text = item.text()
        # Remove old icon if present
        for old_icon in ["⏳", "✓", "✗", "○"]:
            text = text.replace(f"{old_icon} ", "")
        
        item.setText(f"{icon} {text}")
    
    def clear(self):
        """Clear the preview"""
        self.chunks = []
        self.list_widget.clear()
        self.info_label.setText("No content to preview")