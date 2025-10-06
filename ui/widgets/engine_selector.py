"""
Engine Selector Widget
Allows switching between local Chatterbox and API modes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QLineEdit, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal


class EngineSelectorWidget(QGroupBox):
    """Widget for selecting TTS engine type"""
    
    engine_changed = Signal(str)  # Emits "local" or "api"
    
    def __init__(self):
        super().__init__("🔧 TTS Engine")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Local engine option
        self.local_radio = QRadioButton("🏠 Local Chatterbox (Built-in)")
        self.local_radio.setToolTip(
            "Use local Chatterbox model directly.\n"
            "Faster startup, no server required."
        )
        self.local_radio.toggled.connect(self.on_engine_changed)
        layout.addWidget(self.local_radio)
        
        local_info = QLabel("   • No server needed\n   • Uses local GPU/CPU\n   • Better performance")
        local_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(local_info)
        
        # API engine option
        self.api_radio = QRadioButton("🌐 API Server (External)")
        self.api_radio.setToolTip(
            "Connect to external TTS-WebUI server.\n"
            "Useful for distributed setups."
        )
        self.api_radio.toggled.connect(self.on_engine_changed)
        layout.addWidget(self.api_radio)
        
        # API URL input
        api_layout = QHBoxLayout()
        api_layout.addSpacing(20)
        
        api_label = QLabel("API URL:")
        self.api_url_input = QLineEdit("http://localhost:7778/v1")
        self.api_url_input.setPlaceholderText("http://localhost:7778/v1")
        self.api_url_input.setEnabled(False)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_url_input)
        
        layout.addLayout(api_layout)
        
        # Default to local
        self.local_radio.setChecked(True)
    
    def on_engine_changed(self):
        """Called when engine selection changes"""
        # Enable/disable API URL input
        self.api_url_input.setEnabled(self.api_radio.isChecked())
        
        # Emit signal
        engine_type = "api" if self.api_radio.isChecked() else "local"
        self.engine_changed.emit(engine_type)
    
    def get_engine_type(self) -> str:
        """Get selected engine type"""
        return "api" if self.api_radio.isChecked() else "local"
    
    def get_api_url(self) -> str:
        """Get API URL"""
        return self.api_url_input.text()
    
    def set_engine_type(self, engine_type: str):
        """Set engine type"""
        if engine_type == "api":
            self.api_radio.setChecked(True)
        else:
            self.local_radio.setChecked(True)
    
    def set_api_url(self, url: str):
        """Set API URL"""
        self.api_url_input.setText(url)