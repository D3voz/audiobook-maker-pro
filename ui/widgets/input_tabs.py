"""
Input tabs widget for different input methods.
Provides tabs for: Direct Text, Text File, EPUB File
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFileDialog
)
from PySide6.QtCore import Signal


class InputTabsWidget(QTabWidget):
    """
    Tab widget for different input methods.
    Emits signals when content changes or files are selected.
    """
    
    # Signals
    text_changed = Signal(str)      # Emits when text content changes
    file_selected = Signal(str)     # Emits when a file is selected
    
    def __init__(self):
        super().__init__()
        
        self.current_file_path = ""
        
        # Create tabs
        self.create_direct_text_tab()
        self.create_text_file_tab()
        self.create_epub_tab()
        
        # Connect tab change signal
        self.currentChanged.connect(self.on_tab_changed)
    
    def create_direct_text_tab(self):
        """Create the direct text input tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel(
            "📝 Enter or paste text directly below. "
            "This is ideal for short texts or testing."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Enter the text you want to convert to speech...\n\n"
            "You can paste multiple paragraphs here."
        )
        self.text_edit.textChanged.connect(self.on_direct_text_changed)
        layout.addWidget(self.text_edit)
        
        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        layout.addWidget(self.char_count_label)
        
        self.addTab(tab, "📝 Direct Text")
    
    def create_text_file_tab(self):
        """Create the text file input tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel(
            "📄 Select a text file (.txt, .md) to convert to an audiobook."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.text_file_path = QLineEdit()
        self.text_file_path.setReadOnly(True)
        self.text_file_path.setPlaceholderText("No file selected...")
        
        browse_btn = QPushButton("📁 Browse...")
        browse_btn.clicked.connect(self.browse_text_file)
        
        file_layout.addWidget(self.text_file_path)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Drag and drop hint
        hint = QLabel(
            "💡 Tip: You can also drag and drop a file here (feature coming soon)"
        )
        hint.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(hint)
        
        # File info area
        self.text_file_info = QLabel("Select a file to see information...")
        self.text_file_info.setWordWrap(True)
        layout.addWidget(self.text_file_info)
        
        layout.addStretch()
        
        self.addTab(tab, "📄 Text File")
    
    def create_epub_tab(self):
        """Create the EPUB file input tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel(
            "📚 Select an EPUB eBook file to convert to an audiobook."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.epub_file_path = QLineEdit()
        self.epub_file_path.setReadOnly(True)
        self.epub_file_path.setPlaceholderText("No EPUB file selected...")
        
        browse_btn = QPushButton("📁 Browse...")
        browse_btn.clicked.connect(self.browse_epub_file)
        
        file_layout.addWidget(self.epub_file_path)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # File info area
        self.epub_file_info = QLabel("Select an EPUB file to see information...")
        self.epub_file_info.setWordWrap(True)
        layout.addWidget(self.epub_file_info)
        
        layout.addStretch()
        
        self.addTab(tab, "📚 EPUB File")
    
    def browse_text_file(self):
        """Open file dialog to select text file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Text File",
            "",
            "Text Files (*.txt *.md);;All Files (*)"
        )
        
        if filepath:
            self.set_text_file(filepath)
    
    def browse_epub_file(self):
        """Open file dialog to select EPUB file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select EPUB File",
            "",
            "EPUB Files (*.epub);;All Files (*)"
        )
        
        if filepath:
            self.set_epub_file(filepath)
    
    def set_text_file(self, filepath: str):
        """Set the text file path"""
        self.text_file_path.setText(filepath)
        self.current_file_path = filepath
        
        # Show basic file info
        size = os.path.getsize(filepath) / 1024  # KB
        self.text_file_info.setText(
            f"File: {os.path.basename(filepath)}\n"
            f"Size: {size:.1f} KB\n\n"
            f"Click 'Generate Audio' to create audiobook..."
        )
        
        # Switch to this tab
        self.setCurrentIndex(1)
        
        # Emit signal
        self.file_selected.emit(filepath)
    
    def set_epub_file(self, filepath: str):
        """Set the EPUB file path"""
        self.epub_file_path.setText(filepath)
        self.current_file_path = filepath
        
        # Show basic file info
        size = os.path.getsize(filepath) / 1024  # KB
        self.epub_file_info.setText(
            f"File: {os.path.basename(filepath)}\n"
            f"Size: {size:.1f} KB\n\n"
            f"Click 'Generate Audio' to create audiobook..."
        )
        
        # Switch to this tab
        self.setCurrentIndex(2)
        
        # Emit signal
        self.file_selected.emit(filepath)
    
    def on_direct_text_changed(self):
        """Called when direct text changes"""
        text = self.text_edit.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        
        self.char_count_label.setText(
            f"Characters: {char_count:,} | Words: {word_count:,}"
        )
        
        # Emit signal
        self.text_changed.emit(text)
    
    def on_tab_changed(self, index):
        """Called when active tab changes"""
        # Clear signals when switching tabs
        pass
    
    def get_input(self) -> tuple:
        """
        Get current input content.
        
        Returns:
            Tuple of (input_type, content) where:
            - input_type: 'text', 'file', or 'epub'
            - content: The text or file path
        """
        current_index = self.currentIndex()
        
        if current_index == 0:  # Direct text
            text = self.text_edit.toPlainText().strip()
            return ('text', text)
        
        elif current_index == 1:  # Text file
            filepath = self.text_file_path.text()
            return ('file', filepath)
        
        elif current_index == 2:  # EPUB
            filepath = self.epub_file_path.text()
            return ('epub', filepath)
        
        return ('text', '')