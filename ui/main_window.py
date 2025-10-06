"""
Main application window - UPDATED for local/API engine support
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMessageBox, QFileDialog, QStatusBar, QMenuBar, QMenu,
    QPushButton, QLabel, QProgressBar, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence

from core.tts_factory import TTSFactory
from core.tts_base import TTSBase
from core.settings_manager import SettingsManager
from core.audiobook_maker import AudiobookMaker
from workers.audio_generator import AudioGeneratorWorker
from workers.audiobook_generator import AudiobookGeneratorWorker
from workers.file_analyzer import FileAnalyzerWorker

from .widgets.input_tabs import InputTabsWidget
from .widgets.settings_panel import SettingsPanel
from .widgets.chunk_preview import ChunkPreviewWidget
from .widgets.preset_manager import PresetManagerDialog
from .widgets.audio_player import AudioPlayerWidget
from .widgets.voice_manager import VoiceManagerDialog
from .ebook_editor.main_widget import EbookEditorWidget
from .styles import get_stylesheet


class MainWindow(QMainWindow):
    """Main application window with Audiobook Maker and Ebook Editor"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize settings manager first
        self.settings_manager = SettingsManager()
        
        # Initialize TTS engine (will be created after loading settings)
        self.tts_engine: TTSBase = None
        self.audiobook_maker = None
        
        # Worker threads
        self.audio_worker = None
        self.audiobook_worker = None
        self.analyzer_worker = None
        
        # Current audio data
        self.current_audio = None
        
        # Setup UI
        self.setWindowTitle("Audiobook Maker Pro")
        self.setMinimumSize(1200, 850)
        self.setup_ui()
        self.create_menu_bar()
        self.create_status_bar()
        
        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # Load settings and initialize engine
        self.load_last_settings()
        self.initialize_engine()
        
        # Check engine availability
        QTimer.singleShot(500, self.check_engine_status)
    
    def setup_ui(self):
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create main tab widget
        self.main_tabs = QTabWidget()
        
        # Tab 1: Audiobook Maker
        audiobook_tab = self.create_audiobook_maker_tab()
        self.main_tabs.addTab(audiobook_tab, "🎤 Audiobook Maker")
        
        # Tab 2: Ebook Editor
        self.ebook_editor = EbookEditorWidget()
        self.ebook_editor.status_message.connect(self.update_status)
        self.main_tabs.addTab(self.ebook_editor, "📚 Ebook Editor")
        
        main_layout.addWidget(self.main_tabs)
    
    def create_audiobook_maker_tab(self) -> QWidget:
        """Create the audiobook maker tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_tabs = InputTabsWidget()
        left_layout.addWidget(self.input_tabs, stretch=3)
        
        self.chunk_preview = ChunkPreviewWidget()
        left_layout.addWidget(self.chunk_preview, stretch=2)
        
        # Right panel: Settings
        self.settings_panel = SettingsPanel()
        
        # Connect engine selector signal
        self.settings_panel.engine_selector.engine_changed.connect(
            self.on_engine_type_changed
        )
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.settings_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Audio player
        self.create_audio_player_section(layout)
        
        # Control buttons
        self.create_control_buttons(layout)
        
        # Connect signals
        self.connect_signals()
        
        return tab
    
    def create_audio_player_section(self, parent_layout):
        """Create the audio player section"""
        player_group = QGroupBox("🎵 Audio Player")
        player_layout = QVBoxLayout(player_group)
        
        self.audio_player = AudioPlayerWidget()
        player_layout.addWidget(self.audio_player)
        
        parent_layout.addWidget(player_group)
    
    def create_control_buttons(self, parent_layout):
        """Create the main control buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.generate_btn = QPushButton("🎤 Generate Audio")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setMinimumWidth(150)
        self.generate_btn.clicked.connect(self.generate_audio)
        self.generate_btn.setToolTip("Generate audio from input text (Ctrl+G)")
        self.generate_btn.setShortcut(QKeySequence("Ctrl+G"))
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.cancel_btn.setToolTip("Cancel current generation (Esc)")
        self.cancel_btn.setShortcut(QKeySequence("Esc"))
        
        self.save_btn = QPushButton("💾 Save Audio")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_audio)
        self.save_btn.setToolTip("Save generated audio to file (Ctrl+S)")
        self.save_btn.setShortcut(QKeySequence("Ctrl+S"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
        parent_layout.addWidget(self.progress_bar)
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open File...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Audio...", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_audio)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        
        presets_action = QAction("&Manage Presets...", self)
        presets_action.setShortcut(QKeySequence("Ctrl+M"))
        presets_action.triggered.connect(self.manage_presets)
        settings_menu.addAction(presets_action)
        
        voices_action = QAction("&Manage Voices...", self)
        voices_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        voices_action.triggered.connect(self.manage_voices)
        settings_menu.addAction(voices_action)
        
        settings_menu.addSeparator()
        
        reset_action = QAction("&Reset to Defaults", self)
        reset_action.triggered.connect(self.reset_settings)
        settings_menu.addAction(reset_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        status_action = QAction("&Check Engine Status", self)
        status_action.triggered.connect(self.check_engine_status)
        help_menu.addAction(status_action)
        
        cache_action = QAction("&View Model Cache...", self)
        cache_action.triggered.connect(self.show_cache_info)
        help_menu.addAction(cache_action)

    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Engine status indicator
        self.engine_status_label = QLabel("🔴 Engine: Not initialized")
        self.status_bar.addPermanentWidget(self.engine_status_label)
        
        self.update_status("Ready", "info")
    
    def connect_signals(self):
        """Connect signals between widgets"""
        self.input_tabs.file_selected.connect(self.analyze_file)
        self.input_tabs.text_changed.connect(self.update_chunk_preview)
    
    def initialize_engine(self):
        """Initialize TTS engine based on settings"""
        settings = self.settings_panel.get_settings()
        engine_type = settings.get("engine_type", "local")
        api_url = settings.get("api_url", "http://localhost:7778/v1")
        
        try:
            # Cleanup old engine if exists
            if self.tts_engine:
                self.tts_engine.cleanup()
            
            # Create new engine
            self.update_status(f"Initializing {engine_type} engine...", "info")
            self.tts_engine = TTSFactory.create_engine(engine_type, api_url)
            
            # Create audiobook maker with new engine
            self.audiobook_maker = AudiobookMaker(self.tts_engine)
            
            self.update_status(f"{engine_type.title()} engine initialized", "success")
            
        except Exception as e:
            self.update_status(f"Failed to initialize engine: {str(e)}", "error")
            QMessageBox.critical(
                self,
                "Engine Initialization Error",
                f"Could not initialize TTS engine:\n\n{str(e)}\n\n"
                f"The application will use fallback settings."
            )
    
    def on_engine_type_changed(self, engine_type: str):
        """Called when user changes engine type"""
        reply = QMessageBox.question(
            self,
            "Change Engine",
            f"Switch to {engine_type} engine?\n\n"
            f"This will reinitialize the TTS system.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.initialize_engine()
            self.check_engine_status()
    
    def check_engine_status(self):
        """Check if TTS engine is available"""
        if not self.tts_engine:
            self.engine_status_label.setText("🔴 Engine: Not initialized")
            self.update_status("TTS engine not initialized", "error")
            return
        
        try:
            if self.tts_engine.test_connection():
                engine_type = self.settings_panel.engine_selector.get_engine_type()
                self.engine_status_label.setText(f"🟢 Engine: {engine_type.title()} Ready")
                self.update_status(f"{engine_type.title()} engine ready", "success")
            else:
                self.engine_status_label.setText("🟡 Engine: Not available")
                self.update_status("Engine not available", "warning")
                
                # Show different message based on engine type
                engine_type = self.settings_panel.engine_selector.get_engine_type()
                if engine_type == "api":
                    QMessageBox.warning(
                        self,
                        "API Not Available",
                        "Could not connect to TTS API server.\n\n"
                        f"URL: {self.settings_panel.engine_selector.get_api_url()}\n\n"
                        "Please ensure the server is running or switch to Local mode."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Chatterbox Not Available",
                        "Could not load Chatterbox module.\n\n"
                        "Please ensure Chatterbox is installed:\n"
                        "pip install chatterbox-tts\n\n"
                        "Or switch to API mode if you have a remote server."
                    )
        except Exception as e:
            self.engine_status_label.setText("🔴 Engine: Error")
            self.update_status(f"Engine error: {str(e)}", "error")
    
    def generate_audio(self):
        """Generate audio from current input"""
        input_type, content = self.input_tabs.get_input()
        
        if not content:
            QMessageBox.warning(self, "No Input", "Please provide text or select a file first.")
            return
        
        if not self.tts_engine:
            QMessageBox.critical(self, "No Engine", "TTS engine not initialized. Check Settings menu.")
            return
        
        if input_type in ["file", "epub"]:
            self.generate_audiobook(content)
        else:
            self.generate_single_audio(content)
    
    def generate_single_audio(self, text: str):
        """Generate a single audio clip from text"""
        settings = self.settings_panel.get_settings()
        
        tts_settings = {k: v for k, v in settings.items() 
                        if k not in ['engine_type', 'api_url']}

        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating audio...")
        self.update_status("Generating audio...", "info")
        
        self.audio_worker = AudioGeneratorWorker(self.tts_engine, text, settings)
        self.audio_worker.finished.connect(self.on_audio_generated)
        self.audio_worker.error.connect(self.on_generation_error)
        self.audio_worker.progress.connect(self.on_progress_update)
        self.audio_worker.start()
    
    def generate_audiobook(self, filepath: str):
        """Generate full audiobook from file"""
        default_name = f"audiobook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audiobook As",
            default_name,
            "WAV Files (*.wav);;All Files (*)"
        )
        
        if not output_path:
            return
        
        settings = self.settings_panel.get_settings()

        tts_settings = {k: v for k, v in settings.items() 
                        if k not in ['engine_type', 'api_url']}
        
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating audiobook...")
        self.update_status("Generating audiobook...", "info")
        
        self.audiobook_worker = AudiobookGeneratorWorker(
            self.audiobook_maker, filepath, output_path, tts_settings
        )
        self.audiobook_worker.finished.connect(self.on_audiobook_generated)
        self.audiobook_worker.error.connect(self.on_generation_error)
        self.audiobook_worker.progress.connect(self.on_audiobook_progress)
        self.audiobook_worker.start()
    
    def cancel_generation(self):
        """Cancel current generation"""
        if self.audiobook_worker and self.audiobook_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Generation",
                "Are you sure you want to cancel audiobook generation?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.audiobook_worker.cancel()
                self.update_status("Cancelling...", "warning")
    
    def analyze_file(self, filepath: str):
        """Analyze selected file"""
        self.update_status(f"Analyzing file: {os.path.basename(filepath)}", "info")
        
        if not self.audiobook_maker:
            return
        
        self.analyzer_worker = FileAnalyzerWorker(self.audiobook_maker, filepath)
        self.analyzer_worker.finished.connect(self.on_file_analyzed)
        self.analyzer_worker.error.connect(self.on_analysis_error)
        self.analyzer_worker.start()
    
    def update_chunk_preview(self, text: str):
        """Update chunk preview when text changes"""
        if text and self.audiobook_maker:
            chunks = self.audiobook_maker.text_processor.chunk_text(text)
            self.chunk_preview.set_chunks(chunks)
        else:
            self.chunk_preview.clear()
    
    def save_audio(self):
        """Save generated audio to file"""
        if not self.current_audio:
            QMessageBox.warning(self, "No Audio", "Please generate audio first.")
            return
        
        default_name = f"tts_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio As",
            default_name,
            "WAV Files (*.wav);;All Files (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'wb') as f:
                    f.write(self.current_audio)
                
                file_size = len(self.current_audio) / 1024
                self.update_status(f"Audio saved ({file_size:.1f} KB)", "success")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Audio saved successfully!\n\nFile: {filepath}\nSize: {file_size:.1f} KB"
                )
            except Exception as e:
                self.update_status("Failed to save audio", "error")
                QMessageBox.critical(self, "Save Error", f"Could not save file:\n{str(e)}")
    
    def open_file(self):
        """Open file dialog"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            "",
            "Text Files (*.txt);;PDF Files (*.pdf);;EPUB Files (*.epub);;All Files (*)"
        )
        
        if filepath:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.epub':
                self.input_tabs.set_epub_file(filepath)
            else:
                self.input_tabs.set_text_file(filepath)
    
    def manage_presets(self):
        """Show preset management dialog"""
        dialog = PresetManagerDialog(self.settings_manager, self)
        
        if dialog.exec():
            preset_name = dialog.get_selected_preset()
            if preset_name:
                settings = self.settings_manager.load_settings(preset_name)
                if settings:
                    self.settings_panel.apply_settings(settings)
                    self.update_status(f"Loaded preset: {preset_name}", "success")
    
    def manage_voices(self):
        """Show voice manager dialog"""
        dialog = VoiceManagerDialog(self)
        dialog.exec()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings_panel.reset_to_defaults()
            self.update_status("Settings reset to defaults", "warning")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Audiobook Maker Pro",
            "<h2>Audiobook Maker Pro</h2>"
            "<p>Version 2.0.0</p>"
            "<p>A professional desktop application for converting text to audiobooks "
            "using local or remote TTS technology.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>🏠 Local Chatterbox TTS (built-in)</li>"
            "<li>🌐 Remote API support</li>"
            "<li>📁 Multiple input formats (TXT, PDF, EPUB)</li>"
            "<li>🎤 Voice management system</li>"
            "<li>⚙️ Advanced TTS settings</li>"
            "<li>💾 Preset management</li>"
            "<li>📚 Ebook chapter editor</li>"
            "</ul>"
            "<p>Built with PySide6 and Python</p>"
        )

    def show_cache_info(self):
        """Show model cache information dialog"""
        from .widgets.cache_info_dialog import CacheInfoDialog
        dialog = CacheInfoDialog(self)
        dialog.exec()
    
    def load_last_settings(self):
        """Load last used settings"""
        settings = self.settings_manager.load_settings()
        if settings:
            self.settings_panel.apply_settings(settings)
            self.update_status("Loaded last used settings", "success")
    
    def save_current_settings(self):
        """Auto-save current settings"""
        settings = self.settings_panel.get_settings()
        self.settings_manager.save_settings(settings)
    
    # ==================== Worker Callbacks ====================
    
    def on_audio_generated(self, audio_data: bytes):
        """Audio generation completed"""
        self.current_audio = audio_data
        self.audio_player.load_audio(audio_data)
        
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Complete!")
        
        size_kb = len(audio_data) / 1024
        self.update_status(f"Audio generated ({size_kb:.1f} KB)", "success")
        self.save_current_settings()
        
        QMessageBox.information(
            self,
            "Success",
            f"Audio generated successfully!\n\nSize: {size_kb:.1f} KB"
        )
    
    def on_audiobook_generated(self, success: bool, output_path: str):
        """Audiobook generation completed"""
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Complete!")
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            self.update_status(f"Audiobook generated ({file_size:.1f} MB)", "success")
            self.save_current_settings()
            
            QMessageBox.information(
                self,
                "Success",
                f"Audiobook created successfully!\n\n"
                f"File: {output_path}\n"
                f"Size: {file_size:.1f} MB"
            )
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Cancelled")
            self.update_status("Audiobook generation cancelled", "warning")
    
    def on_generation_error(self, error_message: str):
        """Generation failed"""
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Error")
        self.update_status("Generation failed", "error")
        
        QMessageBox.critical(
            self,
            "Generation Error",
            f"Audio generation failed:\n\n{error_message}"
        )
    
    def on_progress_update(self, message: str):
        """Progress update"""
        self.update_status(message, "info")
        self.progress_bar.setFormat(message)
    
    def on_audiobook_progress(self, current: int, total: int, message: str):
        """Audiobook progress update"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{progress}%")
        
        self.update_status(f"{message} ({current}/{total})", "info")
        self.chunk_preview.update_chunk_status(current)
    
    def on_file_analyzed(self, info: dict):
        """File analysis completed"""
        text = info.get('preview', '')
        if text:
            self.update_chunk_preview(text)
        
        chunks = info.get('total_chunks', 0)
        duration = info.get('estimated_duration_minutes', 0)
        self.update_status(
            f"File analyzed: {chunks} chunks, ~{duration:.1f} minutes",
            "success"
        )
    
    def on_analysis_error(self, error_message: str):
        """File analysis failed"""
        self.update_status("File analysis failed", "error")
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Could not analyze file:\n\n{error_message}"
        )
    
    def update_status(self, message: str, status_type: str = "info"):
        """Update status bar"""
        colors = {
            'success': '#00ff00',
            'error': '#ff0000',
            'warning': '#ffff00',
            'info': '#00ffff'
        }
        
        color = colors.get(status_type, colors['info'])
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet(f"color: {color};")
    
    def closeEvent(self, event):
        """Handle window close"""
        # Cleanup audio player
        self.audio_player.cleanup()
        
        # Cleanup voice manager
        if hasattr(self.settings_panel, 'voice_manager'):
            self.settings_panel.voice_manager.cleanup()
        
        # Check for unsaved ebook changes
        if hasattr(self.ebook_editor, 'check_unsaved_changes'):
            if not self.ebook_editor.check_unsaved_changes():
                event.ignore()
                return
        
        # Cancel running workers
        if self.audiobook_worker and self.audiobook_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Close Application",
                "Audiobook generation is in progress. Quit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.audiobook_worker.cancel()
            self.audiobook_worker.wait()
        
        # Cleanup TTS engine
        if self.tts_engine:
            self.tts_engine.cleanup()
        
        # Save settings
        self.save_current_settings()
        
        event.accept()