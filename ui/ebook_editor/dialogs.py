"""
Dialogs for ebook editor operations.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from ebook_editor.core.models import Book
from ebook_editor.utils.splitters import ChapterSplitter


class NewBookDialog(QDialog):
    """Dialog for creating a new book."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("New Book")
        self.setMinimumWidth(400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.author_edit = QLineEdit()
        self.author_edit.setText("Unknown Author")
        author_layout.addWidget(self.author_edit)
        layout.addLayout(author_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("Create")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_data(self) -> tuple:
        """Get dialog data."""
        return self.title_edit.text().strip() or "Untitled", self.author_edit.text().strip()


class MetadataDialog(QDialog):
    """Dialog for editing book metadata."""
    
    def __init__(self, book: Book, parent=None):
        super().__init__(parent)
        
        self.book = book
        
        self.setWindowTitle("Edit Metadata")
        self.setMinimumWidth(400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(self.book.title)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.author_edit = QLineEdit(self.book.author)
        author_layout.addWidget(self.author_edit)
        layout.addLayout(author_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("Save")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_data(self) -> tuple:
        """Get dialog data."""
        return self.title_edit.text().strip(), self.author_edit.text().strip()


class ResplitDialog(QDialog):
    """Dialog for re-splitting PDF/TXT with heuristic preview."""
    
    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        
        self.filepath = filepath
        
        self.setWindowTitle("Re-split Chapters")
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.preview_split()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel("Select a heuristic to detect chapter boundaries:")
        layout.addWidget(info)
        
        # Heuristic selector
        heuristic_layout = QHBoxLayout()
        heuristic_layout.addWidget(QLabel("Heuristic:"))
        
        self.heuristic_combo = QComboBox()
        for key, (pattern, description) in ChapterSplitter.HEURISTICS.items():
            self.heuristic_combo.addItem(description, key)
        self.heuristic_combo.currentIndexChanged.connect(self.preview_split)
        heuristic_layout.addWidget(self.heuristic_combo)
        
        layout.addLayout(heuristic_layout)
        
        # Preview
        preview_label = QLabel("Preview:")
        layout.addWidget(preview_label)
        
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def preview_split(self):
        """Preview the split with selected heuristic."""
        self.preview_list.clear()
        
        heuristic = self.heuristic_combo.currentData()
        
        # Read file content
        try:
            if self.filepath.lower().endswith('.txt'):
                with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read()
            elif self.filepath.lower().endswith('.pdf'):
                import fitz
                doc = fitz.open(self.filepath)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
            else:
                return
            
            # Preview split
            previews = ChapterSplitter.preview_split(text, heuristic)
            
            for i, preview in enumerate(previews):
                item_text = f"{i+1}. {preview['title']} ({preview['length']} chars)\n   {preview['preview']}"
                self.preview_list.addItem(item_text)
            
        except Exception as e:
            self.preview_list.addItem(f"Error: {str(e)}")
    
    def get_selected_heuristic(self) -> str:
        """Get selected heuristic name."""
        return self.heuristic_combo.currentData()


def get_open_filename(parent, title: str, filter: str) -> str:
    """Show open file dialog."""
    filepath, _ = QFileDialog.getOpenFileName(parent, title, "", filter)
    return filepath


def get_save_filename(parent, title: str, default_name: str, filter: str) -> str:
    """Show save file dialog."""
    filepath, _ = QFileDialog.getSaveFileName(parent, title, default_name, filter)
    return filepath