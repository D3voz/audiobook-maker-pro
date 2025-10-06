"""
Main ebook editor widget - integrates all UI components.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QMessageBox, QFileDialog, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from ebook_editor.core.models import Book
from ebook_editor.core.services import EbookService
from .chapter_list import ChapterListWidget
from .chapter_editor import ChapterEditorWidget
from .metadata_panel import MetadataPanel
from .dialogs import (
    NewBookDialog, ResplitDialog, MetadataDialog,
    get_open_filename, get_save_filename
)
from .workers import OpenBookWorker, SaveBookWorker, ExportChapterWorker


class EbookEditorWidget(QWidget):
    """Main widget for ebook chapter extractor and editor."""
    
    # Signals
    status_message = Signal(str, str)  # (message, type)
    
    def __init__(self):
        super().__init__()
        
        self.current_book = None
        self.service = EbookService()
        
        # Workers - keep references to prevent premature destruction
        self.open_worker = None
        self.save_worker = None
        self.export_worker = None  # ADD THIS
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = self.create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Chapter list
        self.chapter_list = ChapterListWidget()
        self.chapter_list.chapter_selected.connect(self.on_chapter_selected)
        self.chapter_list.chapter_moved.connect(self.on_chapter_moved)
        self.chapter_list.chapter_deleted.connect(self.on_chapter_deleted)
        splitter.addWidget(self.chapter_list)
        
        # Center/Right: Editor and metadata
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Metadata panel
        self.metadata_panel = MetadataPanel()
        self.metadata_panel.metadata_changed.connect(self.on_metadata_changed)
        right_layout.addWidget(self.metadata_panel)
        
        # Chapter editor
        self.editor = ChapterEditorWidget()
        self.editor.content_changed.connect(self.on_content_changed)
        right_layout.addWidget(self.editor)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        # Status label
        self.status_label = QLabel("No book open")
        layout.addWidget(self.status_label)
        
        # Initial state
        self.set_book_open_state(False)
    
    def create_toolbar(self) -> QToolBar:
        """Create the toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Open
        open_action = QAction("📖 Open", self)
        open_action.triggered.connect(self.open_book)
        toolbar.addAction(open_action)
        
        # New
        new_action = QAction("📄 New Book", self)
        new_action.triggered.connect(self.new_book)
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        # Save As
        self.save_action = QAction("💾 Save As EPUB", self)
        self.save_action.triggered.connect(self.save_book)
        toolbar.addAction(self.save_action)
        
        # Export Chapter
        self.export_action = QAction("📤 Export Chapter", self)
        self.export_action.triggered.connect(self.export_chapter)
        toolbar.addAction(self.export_action)
        
        # Import Chapter
        self.import_action = QAction("📥 Import Chapter", self)
        self.import_action.triggered.connect(self.import_chapter)
        toolbar.addAction(self.import_action)
        
        toolbar.addSeparator()
        
        # Re-split
        self.resplit_action = QAction("✂️ Re-split", self)
        self.resplit_action.triggered.connect(self.resplit_book)
        toolbar.addAction(self.resplit_action)
        
        # Metadata
        self.metadata_action = QAction("ℹ️ Edit Metadata", self)
        self.metadata_action.triggered.connect(self.edit_metadata)
        toolbar.addAction(self.metadata_action)
        
        return toolbar
    
    def set_book_open_state(self, is_open: bool):
        """Enable/disable actions based on book state."""
        self.save_action.setEnabled(is_open)
        self.export_action.setEnabled(is_open)
        self.import_action.setEnabled(is_open)
        self.metadata_action.setEnabled(is_open)
        self.editor.setEnabled(is_open)
        
        # Re-split only for PDF/TXT
        if is_open and self.current_book and self.current_book.source_path:
            ext = self.current_book.source_path.lower()
            self.resplit_action.setEnabled(ext.endswith(('.pdf', '.txt')))
        else:
            self.resplit_action.setEnabled(False)
    
    def open_book(self):
        """Open an ebook file."""
        filepath = get_open_filename(
            self,
            "Open Ebook",
            "Ebook Files (*.epub *.pdf *.txt);;EPUB Files (*.epub);;PDF Files (*.pdf);;Text Files (*.txt)"
        )
        
        if not filepath:
            return
        
        # Check for unsaved changes
        if not self.check_unsaved_changes():
            return
        
        # Open in worker thread
        self.status_message.emit("Opening book...", "info")
        
        self.open_worker = OpenBookWorker(self.service, filepath)
        self.open_worker.finished.connect(self.on_book_opened)
        self.open_worker.error.connect(self.on_open_error)
        self.open_worker.finished.connect(self.cleanup_open_worker)
        self.open_worker.error.connect(self.cleanup_open_worker)
        self.open_worker.start()
    
    def on_book_opened(self, book: Book):
        """Called when book is opened successfully."""
        self.current_book = book
        self.chapter_list.set_book(book)
        self.metadata_panel.set_book(book)
        self.set_book_open_state(True)
        
        # Select first chapter
        if book.chapters:
            self.chapter_list.select_chapter(0)
        
        self.update_status()
        self.status_message.emit(f"Opened: {book.title}", "success")
    
    def on_open_error(self, error_msg: str):
        """Called when book open fails."""
        self.status_message.emit("Failed to open book", "error")
        QMessageBox.critical(self, "Open Error", f"Failed to open book:\n\n{error_msg}")
    
    def cleanup_open_worker(self):
        """Cleanup open worker."""
        if self.open_worker:
            self.open_worker.deleteLater()
            self.open_worker = None
    
    def new_book(self):
        """Create a new empty book."""
        if not self.check_unsaved_changes():
            return
        
        dialog = NewBookDialog(self)
        if dialog.exec():
            title, author = dialog.get_data()
            
            try:
                self.current_book = self.service.create_new_book(title, author)
                self.chapter_list.set_book(self.current_book)
                self.metadata_panel.set_book(self.current_book)
                self.set_book_open_state(True)
                self.update_status()
                
                self.status_message.emit(f"Created new book: {title}", "success")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create book:\n\n{str(e)}")
    
    def save_book(self):
        """Save book as EPUB."""
        if not self.current_book:
            return
        
        default_name = f"{self.current_book.title}.epub"
        filepath = get_save_filename(
            self,
            "Save As EPUB",
            default_name,
            "EPUB Files (*.epub)"
        )
        
        if not filepath:
            return
        
        # Save current chapter edits
        self.editor.save_current_chapter()
        
        # Save in worker thread
        self.status_message.emit("Saving book...", "info")
        
        self.save_worker = SaveBookWorker(self.service, self.current_book, filepath)
        self.save_worker.finished.connect(self.on_book_saved)
        self.save_worker.error.connect(self.on_save_error)
        self.save_worker.finished.connect(self.cleanup_save_worker)
        self.save_worker.error.connect(self.cleanup_save_worker)
        self.save_worker.start()
    
    def on_book_saved(self):
        """Called when book is saved successfully."""
        self.update_status()
        self.status_message.emit("Book saved successfully", "success")
        QMessageBox.information(self, "Success", "Book saved successfully!")
    
    def on_save_error(self, error_msg: str):
        """Called when book save fails."""
        self.status_message.emit("Failed to save book", "error")
        QMessageBox.critical(self, "Save Error", f"Failed to save book:\n\n{error_msg}")
    
    def cleanup_save_worker(self):
        """Cleanup save worker."""
        if self.save_worker:
            self.save_worker.deleteLater()
            self.save_worker = None
    
    def export_chapter(self):
        """Export current chapter as standalone EPUB."""
        if not self.current_book:
            return
        
        chapter_id = self.chapter_list.get_selected_chapter_id()
        if not chapter_id:
            QMessageBox.warning(self, "No Selection", "Please select a chapter to export.")
            return
        
        chapter = self.current_book.get_chapter_by_id(chapter_id)
        if not chapter:
            return
        
        # Save current edits
        self.editor.save_current_chapter()
        
        default_name = f"{self.current_book.title} - {chapter.title}.epub"
        filepath = get_save_filename(
            self,
            "Export Chapter",
            default_name,
            "EPUB Files (*.epub)"
        )
        
        if not filepath:
            return
        
        # Export in worker thread
        self.status_message.emit("Exporting chapter...", "info")
        
        # Store worker reference to prevent destruction
        self.export_worker = ExportChapterWorker(self.service, self.current_book, chapter_id, filepath)
        self.export_worker.finished.connect(lambda: self.on_chapter_exported(filepath))
        self.export_worker.error.connect(self.on_export_error)
        # IMPORTANT: Clean up worker after completion
        self.export_worker.finished.connect(self.cleanup_export_worker)
        self.export_worker.error.connect(self.cleanup_export_worker)
        self.export_worker.start()
    
    def on_chapter_exported(self, filepath: str):
        """Called when chapter is exported successfully."""
        self.status_message.emit("Chapter exported successfully", "success")
        QMessageBox.information(
            self,
            "Success",
            f"Chapter exported successfully!\n\n{filepath}"
        )
    
    def on_export_error(self, error_msg: str):
        """Called when chapter export fails."""
        self.status_message.emit("Failed to export chapter", "error")
        QMessageBox.critical(self, "Export Error", f"Failed to export chapter:\n\n{error_msg}")
    
    def cleanup_export_worker(self):
        """Cleanup export worker after completion."""
        if self.export_worker:
            self.export_worker.wait()  # Wait for thread to finish
            self.export_worker.deleteLater()
            self.export_worker = None
    
    def import_chapter(self):
        """Import a chapter from EPUB."""
        if not self.current_book:
            return
        
        filepath = get_open_filename(
            self,
            "Import Chapter (Single-Chapter EPUB Only)",
            "EPUB Files (*.epub)"
        )
        
        if not filepath:
            return
        
        try:
            self.service.import_chapter(self.current_book, filepath)
            self.chapter_list.refresh()
            self.update_status()
            
            self.status_message.emit("Chapter imported successfully", "success")
            QMessageBox.information(self, "Success", "Chapter imported successfully!")
            
        except Exception as e:
            self.status_message.emit("Failed to import chapter", "error")
            QMessageBox.critical(self, "Import Error", str(e))
    
    def resplit_book(self):
        """Re-split PDF/TXT with different heuristic."""
        if not self.current_book or not self.current_book.source_path:
            return
        
        dialog = ResplitDialog(self.current_book.source_path, self)
        if dialog.exec():
            heuristic = dialog.get_selected_heuristic()
            
            if not self.check_unsaved_changes():
                return
            
            try:
                new_book = self.service.resplit_text_book(self.current_book, heuristic)
                self.current_book = new_book
                self.chapter_list.set_book(new_book)
                self.metadata_panel.set_book(new_book)
                
                if new_book.chapters:
                    self.chapter_list.select_chapter(0)
                
                self.update_status()
                self.status_message.emit("Book re-split successfully", "success")
                
            except Exception as e:
                QMessageBox.critical(self, "Re-split Error", f"Failed to re-split:\n\n{str(e)}")
    
    def edit_metadata(self):
        """Edit book metadata."""
        if not self.current_book:
            return
        
        dialog = MetadataDialog(self.current_book, self)
        if dialog.exec():
            title, author = dialog.get_data()
            self.current_book.title = title
            self.current_book.author = author
            self.current_book.mark_dirty()
            
            self.metadata_panel.refresh()
            self.update_status()
    
    def on_chapter_selected(self, chapter_id: str):
        """Called when a chapter is selected."""
        if self.current_book:
            chapter = self.current_book.get_chapter_by_id(chapter_id)
            if chapter:
                self.editor.load_chapter(chapter)
    
    def on_chapter_moved(self, from_index: int, to_index: int):
        """Called when a chapter is moved."""
        if self.current_book:
            self.current_book.move_chapter(from_index, to_index)
            self.update_status()
    
    def on_chapter_deleted(self, chapter_id: str):
        """Called when a chapter is deleted."""
        if self.current_book:
            self.current_book.remove_chapter(chapter_id)
            self.chapter_list.refresh()
            self.editor.clear()
            self.update_status()
    
    def on_content_changed(self):
        """Called when chapter content changes."""
        if self.current_book:
            self.current_book.mark_dirty()
            self.update_status()
    
    def on_metadata_changed(self):
        """Called when metadata changes."""
        if self.current_book:
            self.current_book.mark_dirty()
            self.update_status()
    
    def update_status(self):
        """Update status label."""
        if not self.current_book:
            self.status_label.setText("No book open")
            return
        
        dirty_marker = " *" if self.current_book.is_dirty else ""
        chapter_count = len(self.current_book.chapters)
        
        self.status_label.setText(
            f"{self.current_book.title}{dirty_marker} | "
            f"{chapter_count} chapter{'s' if chapter_count != 1 else ''}"
        )
    
    def check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes and prompt user.
        
        Returns:
            True if OK to proceed, False if cancelled
        """
        if self.current_book and self.current_book.is_dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            return reply == QMessageBox.Yes
        
        return True
    
    def cleanup_all_workers(self):
        """Cleanup all workers on widget close."""
        # Wait for and cleanup all workers
        if self.open_worker and self.open_worker.isRunning():
            self.open_worker.wait()
            self.open_worker.deleteLater()
            self.open_worker = None
        
        if self.save_worker and self.save_worker.isRunning():
            self.save_worker.wait()
            self.save_worker.deleteLater()
            self.save_worker = None
        
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.wait()
            self.export_worker.deleteLater()
            self.export_worker = None
    
    def closeEvent(self, event):
        """Handle widget close."""
        if not self.check_unsaved_changes():
            event.ignore()
        else:
            self.cleanup_all_workers()
            event.accept()