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
        self.local_radio = QRadioButton("🏠 Local Chatterbox (Direct)")
        self.local_radio.setToolTip(
            "Run Chatterbox directly in this application.\n\n"
            "Pros:\n"
            "• No external server needed\n"
            "• Optimized CUDA-graph inference\n"
            "• Supports float16/float32/bfloat16\n"
            "• Direct control"
        )
        self.local_radio.toggled.connect(self.on_engine_changed)
        layout.addWidget(self.local_radio)
        
        local_info = QLabel(
            "   • No server required\n"
            "   • Uses the optimized Chatterbox backend directly\n"
            "   • Recommended for local generation"
        )
        local_info.setWordWrap(True)
        local_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(local_info)
        
        # API engine option
        self.api_radio = QRadioButton("🌐 API Server (TTS-WebUI)")
        self.api_radio.setToolTip(
            "Connect to TTS-WebUI server (local or remote).\n\n"
            "Pros:\n"
            "• Can use a GPU on another computer\n"
            "• Compatible with an existing TTS-WebUI setup\n\n"
            "Cons:\n"
            "• Requires running TTS-WebUI server\n"
            "• Additional setup step"
        )
        self.api_radio.toggled.connect(self.on_engine_changed)
        layout.addWidget(self.api_radio)
        
        # API description
        api_info = QLabel(
            "   • Optional remote-server mode\n"
            "   • Useful when the GPU is on another machine"
        )
        api_info.setWordWrap(True)
        api_info.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        layout.addWidget(api_info)
        
        # API URL input
        api_layout = QHBoxLayout()
        api_layout.addSpacing(20)
        
        api_label = QLabel("Server URL:")
        self.api_url_input = QLineEdit("http://localhost:7778/v1")
        self.api_url_input.setMinimumWidth(170)
        self.api_url_input.setPlaceholderText("http://localhost:7778/v1")
        self.api_url_input.setEnabled(False)
        self.api_url_input.setToolTip(
            "TTS-WebUI API endpoint\n\n"
            "Local server: http://localhost:7778/v1\n"
            "Remote server: http://YOUR_SERVER_IP:7778/v1"
        )
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_url_input)
        
        layout.addLayout(api_layout)
        
        # Help text
        help_text = QLabel(
            "💡 <b>Tip:</b> Local mode now uses the same optimized Chatterbox "
            "inference backend without requiring TTS-WebUI."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #2196F3; font-size: 11px; padding: 5px; margin-top: 10px;")
        layout.addWidget(help_text)
        
        # Local mode is self-contained and uses the optimized backend.
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
