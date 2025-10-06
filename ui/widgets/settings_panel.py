"""
Settings Panel Widget
Contains all TTS configuration options with organized sections.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
    QScrollArea, QLabel, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from .engine_selector import EngineSelectorWidget
from .voice_manager import VoiceManagerWidget


class SettingsPanel(QScrollArea):
    """
    Scrollable panel containing all TTS settings.
    Organized into logical groups for better UX.
    """
    
    settings_changed = Signal(dict)  # Emits when settings change
    
    def __init__(self):
        super().__init__()
        
        # Make scrollable
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # ==================== Engine Selection ====================
        self.engine_selector = EngineSelectorWidget()
        layout.addWidget(self.engine_selector)
        
        # ==================== Model Settings ====================
        model_group = QGroupBox("🤖 Model Settings")
        model_layout = QFormLayout(model_group)
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(["chatterbox", "multilingual"])
        self.model_combo.setToolTip("Select TTS model variant")
        model_layout.addRow("Model:", self.model_combo)
        
        # Device selection
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cuda", "cpu", "mps"])
        self.device_combo.setToolTip("Select device (auto recommended)")
        model_layout.addRow("Device:", self.device_combo)
        
        # Data type
        self.dtype_combo = QComboBox()
        self.dtype_combo.addItems(["float16", "float32", "bfloat16"])
        self.dtype_combo.setCurrentText("float16")
        self.dtype_combo.setToolTip("Lower precision = faster, less VRAM")
        model_layout.addRow("Precision:", self.dtype_combo)
        
        # Compilation
        self.compile_checkbox = QCheckBox("Enable torch.compile")
        self.compile_checkbox.setToolTip("May improve performance (experimental)")
        model_layout.addRow("Optimization:", self.compile_checkbox)
        
        layout.addWidget(model_group)
        
        # ==================== Voice Settings ====================
        voice_group = QGroupBox("🎤 Voice Settings")
        voice_layout = QVBoxLayout(voice_group)
        
        # Voice manager widget
        self.voice_manager = VoiceManagerWidget()
        voice_layout.addWidget(self.voice_manager)
        
        # Or manual path input
        voice_path_layout = QHBoxLayout()
        voice_path_layout.addWidget(QLabel("Manual Path:"))
        
        self.voice_path_input = QLineEdit()
        self.voice_path_input.setPlaceholderText("Or enter voice file path...")
        voice_path_layout.addWidget(self.voice_path_input)
        
        browse_btn = QPushButton("📁")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self.browse_voice_file)
        voice_path_layout.addWidget(browse_btn)
        
        voice_layout.addLayout(voice_path_layout)
        
        # Connect voice manager selection to path input
        self.voice_manager.voice_selected.connect(self.voice_path_input.setText)
        
        layout.addWidget(voice_group)
        
        # ==================== Generation Settings ====================
        gen_group = QGroupBox("🎛️ Generation Settings")
        gen_layout = QFormLayout(gen_group)
        
        # Exaggeration
        self.exaggeration_spin = QDoubleSpinBox()
        self.exaggeration_spin.setRange(0.0, 1.0)
        self.exaggeration_spin.setSingleStep(0.1)
        self.exaggeration_spin.setValue(0.5)
        self.exaggeration_spin.setToolTip("Voice expressiveness (0.0 = flat, 1.0 = very expressive)")
        gen_layout.addRow("Exaggeration:", self.exaggeration_spin)
        
        # CFG Weight
        self.cfg_weight_spin = QDoubleSpinBox()
        self.cfg_weight_spin.setRange(0.0, 10.0)
        self.cfg_weight_spin.setSingleStep(0.5)
        self.cfg_weight_spin.setValue(0.5)
        self.cfg_weight_spin.setToolTip("Classifier-free guidance weight")
        gen_layout.addRow("CFG Weight:", self.cfg_weight_spin)
        
        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.8)
        self.temperature_spin.setToolTip("Randomness (lower = more consistent)")
        gen_layout.addRow("Temperature:", self.temperature_spin)
        
        # Seed
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(-1, 999999)
        self.seed_spin.setValue(-1)
        self.seed_spin.setToolTip("-1 for random seed")
        gen_layout.addRow("Seed:", self.seed_spin)
        
        layout.addWidget(gen_group)
        
        # ==================== Chunking Settings ====================
        chunk_group = QGroupBox("📄 Text Chunking")
        chunk_layout = QFormLayout(chunk_group)
        
        # Split chunks
        self.split_chunks_checkbox = QCheckBox("Split long text into chunks")
        self.split_chunks_checkbox.setChecked(True)
        self.split_chunks_checkbox.setToolTip("Recommended for better quality")
        chunk_layout.addRow("Enable:", self.split_chunks_checkbox)
        
        # Desired length
        self.desired_length_spin = QSpinBox()
        self.desired_length_spin.setRange(50, 500)
        self.desired_length_spin.setValue(200)
        self.desired_length_spin.setToolTip("Target characters per chunk")
        chunk_layout.addRow("Desired Length:", self.desired_length_spin)
        
        # Max length
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(100, 1000)
        self.max_length_spin.setValue(300)
        self.max_length_spin.setToolTip("Maximum characters per chunk")
        chunk_layout.addRow("Max Length:", self.max_length_spin)
        
        # Halve first chunk
        self.halve_first_checkbox = QCheckBox("Halve first chunk")
        self.halve_first_checkbox.setToolTip("Useful for better voice initialization")
        chunk_layout.addRow("Optimization:", self.halve_first_checkbox)
        
        layout.addWidget(chunk_group)
        
        # ==================== Advanced Settings ====================
        advanced_group = QGroupBox("⚙️ Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Max new tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 5000)
        self.max_tokens_spin.setValue(1000)
        self.max_tokens_spin.setToolTip("Maximum tokens to generate")
        advanced_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Cache length
        self.cache_length_spin = QSpinBox()
        self.cache_length_spin.setRange(500, 5000)
        self.cache_length_spin.setValue(1500)
        self.cache_length_spin.setToolTip("Affects T3 speed - higher may be faster")
        advanced_layout.addRow("Cache Length:", self.cache_length_spin)
        
        layout.addWidget(advanced_group)
        
        # ==================== Preset Buttons ====================
        preset_layout = QHBoxLayout()
        
        save_preset_btn = QPushButton("💾 Save Preset")
        save_preset_btn.clicked.connect(self.save_as_preset)
        preset_layout.addWidget(save_preset_btn)
        
        reset_btn = QPushButton("🔄 Reset Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        preset_layout.addWidget(reset_btn)
        
        layout.addLayout(preset_layout)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def browse_voice_file(self):
        """Browse for voice reference file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voice Reference",
            "",
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        )
        
        if file_path:
            self.voice_path_input.setText(file_path)
    
    def get_settings(self) -> dict:
        """
        Get all current settings as a dictionary.
        
        Returns:
            dict: All settings
        """
        # Get voice path - prefer manual input if set, otherwise use selected
        voice_path = self.voice_path_input.text().strip()
        if not voice_path:
            voice_path = self.voice_manager.get_selected_voice()
        
        settings = {
            # Engine settings
            "engine_type": self.engine_selector.get_engine_type(),
            "api_url": self.engine_selector.get_api_url(),
            
            # Model settings
            "model": self.model_combo.currentText(),
            "device": self.device_combo.currentText(),
            "data_type": self.dtype_combo.currentText(),
            "use_compilation": self.compile_checkbox.isChecked(),
            
            # Voice settings
            "voice": voice_path,
            
            # Generation settings
            "exaggeration": self.exaggeration_spin.value(),
            "cfg_weight": self.cfg_weight_spin.value(),
            "temperature": self.temperature_spin.value(),
            "seed": self.seed_spin.value(),
            
            # Chunking settings
            "split_chunks": self.split_chunks_checkbox.isChecked(),
            "desired_length": self.desired_length_spin.value(),
            "max_length": self.max_length_spin.value(),
            "halve_first_chunk": self.halve_first_checkbox.isChecked(),
            
            # Advanced settings
            "max_new_tokens": self.max_tokens_spin.value(),
            "cache_length": self.cache_length_spin.value(),
        }
        
        return settings
    
    def apply_settings(self, settings: dict):
        """
        Apply settings from a dictionary.
        
        Args:
            settings: Dictionary of settings to apply
        """
        # Engine settings
        if "engine_type" in settings:
            self.engine_selector.set_engine_type(settings["engine_type"])
        if "api_url" in settings:
            self.engine_selector.set_api_url(settings["api_url"])
        
        # Model settings
        if "model" in settings:
            index = self.model_combo.findText(settings["model"])
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
        
        if "device" in settings:
            index = self.device_combo.findText(settings["device"])
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        
        if "data_type" in settings:
            index = self.dtype_combo.findText(settings["data_type"])
            if index >= 0:
                self.dtype_combo.setCurrentIndex(index)
        
        if "use_compilation" in settings:
            self.compile_checkbox.setChecked(settings["use_compilation"])
        
        # Voice settings
        if "voice" in settings:
            self.voice_path_input.setText(settings["voice"])
            # Try to select in voice manager if it exists there
            self.voice_manager.set_selected_voice(settings["voice"])
        
        # Generation settings
        if "exaggeration" in settings:
            self.exaggeration_spin.setValue(settings["exaggeration"])
        if "cfg_weight" in settings:
            self.cfg_weight_spin.setValue(settings["cfg_weight"])
        if "temperature" in settings:
            self.temperature_spin.setValue(settings["temperature"])
        if "seed" in settings:
            self.seed_spin.setValue(settings["seed"])
        
        # Chunking settings
        if "split_chunks" in settings:
            self.split_chunks_checkbox.setChecked(settings["split_chunks"])
        if "desired_length" in settings:
            self.desired_length_spin.setValue(settings["desired_length"])
        if "max_length" in settings:
            self.max_length_spin.setValue(settings["max_length"])
        if "halve_first_chunk" in settings:
            self.halve_first_checkbox.setChecked(settings["halve_first_chunk"])
        
        # Advanced settings
        if "max_new_tokens" in settings:
            self.max_tokens_spin.setValue(settings["max_new_tokens"])
        if "cache_length" in settings:
            self.cache_length_spin.setValue(settings["cache_length"])
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        defaults = {
            "engine_type": "local",
            "api_url": "http://localhost:7778/v1",
            "model": "chatterbox",
            "device": "auto",
            "data_type": "float16",
            "use_compilation": False,
            "voice": "",
            "exaggeration": 0.5,
            "cfg_weight": 0.5,
            "temperature": 0.8,
            "seed": -1,
            "split_chunks": True,
            "desired_length": 200,
            "max_length": 300,
            "halve_first_chunk": False,
            "max_new_tokens": 1000,
            "cache_length": 1500,
        }
        
        self.apply_settings(defaults)
        self.settings_changed.emit(defaults)
    
    def save_as_preset(self):
        """Save current settings as a preset"""
        # This will be handled by the main window's preset manager
        # Just emit the signal
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'voice_manager'):
            self.voice_manager.cleanup()