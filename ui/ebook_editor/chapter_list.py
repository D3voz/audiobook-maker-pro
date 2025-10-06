"""
Chapter list widget with drag-drop reordering.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from ebook_editor.core.models import Book


class ChapterListWidget(QWidget):
    """
    Chapter list with reordering capabilities.
    """
    
    # Signals
    chapter_selected = Signal(str)  # chapter_id
    chapter_moved = Signal(int, int)  # from_index, to_index
    chapter_deleted = Signal(str)  # chapter_id
    
    def __init__(self):
        super().__init__()
        
        self.book = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📚 Chapters")
        header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(header)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.currentItemChanged.connect(self.on_item_changed)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.up_btn = QPushButton("⬆ Up")
        self.up_btn.clicked.connect(self.move_up)
        button_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton("⬇ Down")
        self.down_btn.clicked.connect(self.move_down)
        button_layout.addWidget(self.down_btn)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.delete_chapter)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        self.info_label = QLabel("No chapters")
        self.info_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.info_label)
        
        self.update_button_states()
    
    def set_book(self, book: Book):
        """Set the book to display."""
        self.book = book
        self.refresh()
    
    def refresh(self):
        """Refresh the chapter list."""
        self.list_widget.clear()
        
        if not self.book or not self.book.chapters:
            self.info_label.setText("No chapters")
            self.update_button_states()
            return
        
        # Sort by order
        sorted_chapters = sorted(self.book.chapters, key=lambda c: c.order)
        
        for chapter in sorted_chapters:
            item = QListWidgetItem(f"{chapter.order + 1}. {chapter.title}")
            item.setData(Qt.UserRole, chapter.id)
            self.list_widget.addItem(item)
        
        self.info_label.setText(f"{len(self.book.chapters)} chapter(s)")
        self.update_button_states()
    
    def on_item_changed(self, current, previous):
        """Called when selection changes."""
        if current:
            chapter_id = current.data(Qt.UserRole)
            self.chapter_selected.emit(chapter_id)
        
        self.update_button_states()
    
    def on_rows_moved(self, parent, start, end, destination, row):
        """Called when rows are moved via drag-drop."""
        # Calculate new indices
        if row > start:
            to_index = row - 1
        else:
            to_index = row
        
        self.chapter_moved.emit(start, to_index)
        self.refresh()
    
    def move_up(self):
        """Move selected chapter up."""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            self.chapter_moved.emit(current_row, current_row - 1)
            self.refresh()
            self.list_widget.setCurrentRow(current_row - 1)
    
    def move_down(self):
        """Move selected chapter down."""
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            self.chapter_moved.emit(current_row, current_row + 1)
            self.refresh()
            self.list_widget.setCurrentRow(current_row + 1)
    
    def delete_chapter(self):
        """Delete selected chapter."""
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
        
        chapter_id = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Delete Chapter",
            "Are you sure you want to delete this chapter?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chapter_deleted.emit(chapter_id)
    
    def select_chapter(self, index: int):
        """Select chapter by index."""
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)
    
    def get_selected_chapter_id(self) -> str:
        """Get selected chapter ID."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return ""
    
    def update_button_states(self):
        """Update button enabled states."""
        has_selection = self.list_widget.currentItem() is not None
        current_row = self.list_widget.currentRow()
        count = self.list_widget.count()
        
        self.up_btn.setEnabled(has_selection and current_row > 0)
        self.down_btn.setEnabled(has_selection and current_row < count - 1)
        self.delete_btn.setEnabled(has_selection)