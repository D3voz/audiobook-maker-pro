"""
Preset manager dialog for saving/loading/deleting presets.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt

from core.settings_manager import SettingsManager


class PresetManagerDialog(QDialog):
    """
    Dialog for managing TTS presets.
    Allows users to save, load, and delete presets.
    """
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.selected_preset = None
        
        self.setWindowTitle("Manage Presets")
        self.setMinimumSize(400, 500)
        
        self.setup_ui()
        self.load_presets()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📁 Preset Manager")
        header.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(header)
        
        # Info
        info = QLabel(
            "Presets allow you to save and reuse your favorite TTS settings."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # List of presets
        self.preset_list = QListWidget()
        self.preset_list.itemDoubleClicked.connect(self.load_preset)
        layout.addWidget(self.preset_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("✓ Load Selected")
        load_btn.clicked.connect(self.load_preset)
        button_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.clicked.connect(self.delete_preset)
        button_layout.addWidget(delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_presets(self):
        """Load and display available presets"""
        self.preset_list.clear()
        
        presets = self.settings_manager.get_preset_list()
        
        if not presets:
            item_text = "(No presets saved yet)"
            self.preset_list.addItem(item_text)
            return
        
        for preset in presets:
            self.preset_list.addItem(preset)
    
    def load_preset(self):
        """Load the selected preset"""
        current_item = self.preset_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a preset to load.")
            return
        
        preset_name = current_item.text()
        
        if preset_name.startswith("("):
            return  # Empty list message
        
        self.selected_preset = preset_name
        self.accept()
    
    def delete_preset(self):
        """Delete the selected preset"""
        current_item = self.preset_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a preset to delete.")
            return
        
        preset_name = current_item.text()
        
        if preset_name.startswith("("):
            return  # Empty list message
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.settings_manager.delete_preset(preset_name):
                QMessageBox.information(self, "Success", f"Preset '{preset_name}' deleted.")
                self.load_presets()  # Refresh list
            else:
                QMessageBox.critical(self, "Error", "Failed to delete preset.")
    
    def get_selected_preset(self):
        """Get the name of the selected preset"""
        return self.selected_preset