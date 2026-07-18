"""Compact TTS engine selector with optional-runtime controls."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EngineSelectorWidget(QGroupBox):
    """Choose an engine and expose only the controls that engine needs."""

    engine_changed = Signal(str)
    install_requested = Signal()

    ENGINE_NAMES = {
        "local": "Local Chatterbox",
        "qwen3": "Faster Qwen3-TTS",
        "api": "Remote API",
    }

    def __init__(self):
        super().__init__("TTS Engine")
        self._qwen_installed = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Local Chatterbox · built in", "local")
        self.engine_combo.addItem("Faster Qwen3-TTS · CUDA graphs", "qwen3")
        self.engine_combo.addItem("Remote TTS-WebUI API", "api")
        self.engine_combo.setToolTip("Choose the voice engine used for generation.")
        layout.addWidget(self.engine_combo)

        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("mutedLabel")
        layout.addWidget(self.description)

        self.qwen_runtime_widget = QWidget()
        qwen_layout = QVBoxLayout(self.qwen_runtime_widget)
        qwen_layout.setContentsMargins(0, 4, 0, 0)
        qwen_layout.setSpacing(7)
        self.qwen_status = QLabel("Checking optional engine...")
        self.qwen_status.setWordWrap(True)
        qwen_layout.addWidget(self.qwen_status)
        self.install_button = QPushButton("Install Engine")
        self.install_button.setObjectName("secondaryButton")
        self.install_button.clicked.connect(self.install_requested)
        qwen_layout.addWidget(self.install_button)
        layout.addWidget(self.qwen_runtime_widget)

        self.api_widget = QWidget()
        api_layout = QVBoxLayout(self.api_widget)
        api_layout.setContentsMargins(0, 4, 0, 0)
        api_layout.setSpacing(5)
        api_layout.addWidget(QLabel("Server URL"))
        self.api_url_input = QLineEdit("http://localhost:7778/v1")
        self.api_url_input.setPlaceholderText("http://localhost:7778/v1")
        self.api_url_input.setToolTip("OpenAI-compatible TTS-WebUI endpoint")
        api_layout.addWidget(self.api_url_input)
        layout.addWidget(self.api_widget)

        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self._on_engine_changed()

    def _on_engine_changed(self):
        engine_type = self.get_engine_type()
        descriptions = {
            "local": (
                "Fast local Chatterbox generation with no server. Its model stays "
                "inside the main app runtime."
            ),
            "qwen3": (
                "Voice clone, built-in speakers, and voice design through the "
                "CUDA-graph accelerated Qwen engine."
            ),
            "api": (
                "Connect to a TTS-WebUI server on this computer or another machine."
            ),
        }
        self.description.setText(descriptions[engine_type])
        self.qwen_runtime_widget.setVisible(engine_type == "qwen3")
        self.api_widget.setVisible(engine_type == "api")
        self.engine_changed.emit(engine_type)

    def get_engine_type(self) -> str:
        return self.engine_combo.currentData() or "local"

    def get_engine_name(self, engine_type: str = None) -> str:
        return self.ENGINE_NAMES.get(engine_type or self.get_engine_type(), "TTS")

    def get_api_url(self) -> str:
        return self.api_url_input.text().strip()

    def set_engine_type(self, engine_type: str):
        index = self.engine_combo.findData(engine_type)
        if index < 0:
            index = self.engine_combo.findData("local")
        self.engine_combo.setCurrentIndex(index)

    def set_api_url(self, url: str):
        self.api_url_input.setText(url)

    def refresh_selection(self):
        """Refresh dependent controls and notify listeners of the current choice."""
        self._on_engine_changed()

    def set_qwen_runtime_state(self, installed: bool, status: str = ""):
        self._qwen_installed = installed
        self.qwen_status.setText(status or ("Installed" if installed else "Not installed"))
        self.qwen_status.setProperty("statusType", "success" if installed else "warning")
        self.qwen_status.style().unpolish(self.qwen_status)
        self.qwen_status.style().polish(self.qwen_status)
        self.install_button.setText("Repair / Update Engine" if installed else "Install Engine")

    def set_installing(self, installing: bool):
        self.install_button.setEnabled(not installing)
        self.install_button.setText("Installing..." if installing else (
            "Repair / Update Engine" if self._qwen_installed else "Install Engine"
        ))
