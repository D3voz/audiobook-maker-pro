"""
Voice Manager Widget
Manages voice reference files for TTS generation.
"""

import os
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox,
    QDialog, QDialogButtonBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl


class VoiceManagerWidget(QWidget):
    """Widget for managing voice reference files"""
    
    voice_selected = Signal(str)  # Emits selected voice path
    
    def __init__(self, voices_dir: str = "voices"):
        super().__init__()
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(exist_ok=True)
        
        # Audio player for previewing voices
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.setup_ui()
        self.refresh_voices()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎤 Voice References")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Voice list
        self.voice_list = QListWidget()
        self.voice_list.itemClicked.connect(self.on_voice_selected)
        self.voice_list.itemDoubleClicked.connect(self.preview_voice)
        layout.addWidget(self.voice_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add Voice")
        self.add_btn.clicked.connect(self.add_voice)
        
        self.preview_btn = QPushButton("▶️ Preview")
        self.preview_btn.clicked.connect(self.preview_voice)
        self.preview_btn.setEnabled(False)
        
        self.remove_btn = QPushButton("🗑️ Remove")
        self.remove_btn.clicked.connect(self.remove_voice)
        self.remove_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.remove_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        self.info_label = QLabel("Tip: Double-click to preview a voice")
        self.info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.info_label)
    
    def refresh_voices(self):
        """Refresh the list of available voices"""
        self.voice_list.clear()
        
        if not self.voices_dir.exists():
            return
        
        # Find all WAV files
        voice_files = list(self.voices_dir.glob("*.wav"))
        
        for voice_file in sorted(voice_files):
            item = QListWidgetItem(voice_file.stem)
            item.setData(Qt.UserRole, str(voice_file))
            self.voice_list.addItem(item)
        
        # Update info label
        count = len(voice_files)
        self.info_label.setText(f"{count} voice(s) available")
    
    def add_voice(self):
        """Add a new voice file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voice File",
            "",
            "WAV Files (*.wav);;All Audio Files (*.wav *.mp3 *.flac)"
        )
        
        if not file_path:
            return
        
        # Copy file to voices directory
        source = Path(file_path)
        destination = self.voices_dir / source.name
        
        # Check if file already exists
        if destination.exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"Voice '{source.name}' already exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        try:
            shutil.copy2(source, destination)
            self.refresh_voices()
            QMessageBox.information(
                self,
                "Success",
                f"Voice '{source.name}' added successfully!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not add voice:\n{str(e)}"
            )
    
    def remove_voice(self):
        """Remove selected voice"""
        current_item = self.voice_list.currentItem()
        if not current_item:
            return
        
        voice_name = current_item.text()
        voice_path = Path(current_item.data(Qt.UserRole))
        
        reply = QMessageBox.question(
            self,
            "Remove Voice",
            f"Are you sure you want to remove '{voice_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                voice_path.unlink()
                self.refresh_voices()
                self.preview_btn.setEnabled(False)
                self.remove_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not remove voice:\n{str(e)}"
                )
    
    def preview_voice(self):
        """Preview selected voice"""
        current_item = self.voice_list.currentItem()
        if not current_item:
            return
        
        voice_path = current_item.data(Qt.UserRole)
        
        # Stop current playback
        self.player.stop()
        
        # Play voice
        self.player.setSource(QUrl.fromLocalFile(voice_path))
        self.player.play()
    
    def on_voice_selected(self, item: QListWidgetItem):
        """Called when a voice is selected"""
        voice_path = item.data(Qt.UserRole)
        
        self.preview_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        
        # Emit signal
        self.voice_selected.emit(voice_path)
    
    def get_selected_voice(self) -> str:
        """Get the currently selected voice path"""
        current_item = self.voice_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return ""
    
    def set_selected_voice(self, voice_path: str):
        """Select a voice by path"""
        for i in range(self.voice_list.count()):
            item = self.voice_list.item(i)
            if item.data(Qt.UserRole) == voice_path:
                self.voice_list.setCurrentItem(item)
                return
    
    def cleanup(self):
        """Cleanup resources"""
        self.player.stop()


class VoiceManagerDialog(QDialog):
    """Dialog for managing voices"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Manager")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        self.voice_manager = VoiceManagerWidget()
        layout.addWidget(self.voice_manager)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def get_selected_voice(self) -> str:
        """Get selected voice path"""
        return self.voice_manager.get_selected_voice()