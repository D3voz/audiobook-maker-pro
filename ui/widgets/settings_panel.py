"""Capability-aware settings panel for the available TTS engines."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .engine_selector import EngineSelectorWidget
from .voice_manager import VoiceManagerWidget


class SettingsPanel(QScrollArea):
    """Show common settings plus only the controls supported by the engine."""

    settings_changed = Signal(dict)

    QWEN_MODELS = {
        "clone": [
            ("0.6B Base · fastest", "Qwen/Qwen3-TTS-12Hz-0.6B-Base"),
            ("1.7B Base · higher quality", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"),
        ],
        "custom": [
            ("0.6B Custom Voice · fastest", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"),
            ("1.7B Custom Voice · higher quality", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"),
        ],
        "design": [
            ("1.7B Voice Design", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"),
        ],
    }

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(370)
        self.setMaximumWidth(430)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("settingsPanel")

        content = QWidget()
        content.setObjectName("settingsContent")
        content.setMinimumWidth(338)
        self.setWidget(content)
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        self.engine_selector = EngineSelectorWidget()
        self.layout.addWidget(self.engine_selector)

        self._build_chatterbox_settings()
        self._build_qwen_settings()
        self._build_chunk_settings()
        self._build_preset_buttons()
        self.layout.addStretch()

        self.qwen_mode_combo.currentIndexChanged.connect(self._on_qwen_mode_changed)
        self.engine_selector.engine_changed.connect(self._on_engine_changed)
        self._on_qwen_mode_changed()
        self._on_engine_changed(self.engine_selector.get_engine_type())

    def _build_chatterbox_settings(self):
        self.chatterbox_model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(self.chatterbox_model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["chatterbox", "multilingual"])
        model_layout.addRow("Model:", self.model_combo)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "cuda", "cpu", "mps"])
        model_layout.addRow("Device:", self.device_combo)

        self.dtype_combo = QComboBox()
        self.dtype_combo.addItems(["float16", "float32", "bfloat16"])
        self.dtype_combo.setCurrentText("bfloat16")
        model_layout.addRow("Precision:", self.dtype_combo)

        self.compile_checkbox = QCheckBox("Compile initial model pass")
        self.compile_checkbox.setToolTip(
            "The optimized CUDA-graph token generation path remains automatic."
        )
        model_layout.addRow("Optimization:", self.compile_checkbox)
        self.layout.addWidget(self.chatterbox_model_group)

        self.chatterbox_voice_group = QGroupBox("Voice Settings")
        voice_layout = QVBoxLayout(self.chatterbox_voice_group)
        self.voice_manager = VoiceManagerWidget()
        voice_layout.addWidget(self.voice_manager)

        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("Manual path"))
        self.voice_path_input = QLineEdit()
        self.voice_path_input.setPlaceholderText("Optional voice reference...")
        voice_row.addWidget(self.voice_path_input)
        browse = QPushButton("Browse")
        browse.setMaximumWidth(72)
        browse.clicked.connect(lambda: self._browse_audio(self.voice_path_input))
        voice_row.addWidget(browse)
        voice_layout.addLayout(voice_row)
        self.voice_manager.voice_selected.connect(self.voice_path_input.setText)
        self.layout.addWidget(self.chatterbox_voice_group)

        self.chatterbox_generation_group = QGroupBox("Generation Settings")
        generation_layout = QFormLayout(self.chatterbox_generation_group)

        self.exaggeration_spin = QDoubleSpinBox()
        self.exaggeration_spin.setRange(0.0, 1.0)
        self.exaggeration_spin.setSingleStep(0.1)
        self.exaggeration_spin.setValue(0.5)
        generation_layout.addRow("Exaggeration:", self.exaggeration_spin)

        self.cfg_weight_spin = QDoubleSpinBox()
        self.cfg_weight_spin.setRange(0.0, 10.0)
        self.cfg_weight_spin.setSingleStep(0.1)
        self.cfg_weight_spin.setValue(0.5)
        generation_layout.addRow("CFG weight:", self.cfg_weight_spin)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.8)
        generation_layout.addRow("Temperature:", self.temperature_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(-1, 999999)
        self.seed_spin.setValue(-1)
        self.seed_spin.setToolTip("-1 chooses a random seed")
        generation_layout.addRow("Seed:", self.seed_spin)
        self.layout.addWidget(self.chatterbox_generation_group)

        self.chatterbox_advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(self.chatterbox_advanced_group)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 5000)
        self.max_tokens_spin.setValue(1000)
        advanced_layout.addRow("Max tokens:", self.max_tokens_spin)
        self.cache_length_spin = QSpinBox()
        self.cache_length_spin.setRange(500, 5000)
        self.cache_length_spin.setValue(1500)
        advanced_layout.addRow("Cache length:", self.cache_length_spin)
        self.layout.addWidget(self.chatterbox_advanced_group)

    def _build_qwen_settings(self):
        self.qwen_model_group = QGroupBox("Qwen Model & Mode")
        model_layout = QFormLayout(self.qwen_model_group)

        self.qwen_mode_combo = QComboBox()
        self.qwen_mode_combo.addItem("Voice Clone", "clone")
        self.qwen_mode_combo.addItem("Built-in Voice", "custom")
        self.qwen_mode_combo.addItem("Voice Design", "design")
        model_layout.addRow("Mode:", self.qwen_mode_combo)

        self.qwen_model_combo = QComboBox()
        model_layout.addRow("Model:", self.qwen_model_combo)

        self.qwen_language_combo = QComboBox()
        self.qwen_language_combo.setEditable(True)
        self.qwen_language_combo.addItems(
            [
                "Auto", "English", "Chinese", "Japanese", "Korean", "German",
                "French", "Russian", "Portuguese", "Spanish", "Italian",
            ]
        )
        model_layout.addRow("Language:", self.qwen_language_combo)

        self.qwen_dtype_combo = QComboBox()
        self.qwen_dtype_combo.addItems(["bfloat16", "float16"])
        model_layout.addRow("Precision:", self.qwen_dtype_combo)
        cuda_note = QLabel("NVIDIA CUDA is required by this accelerated backend.")
        cuda_note.setWordWrap(True)
        cuda_note.setObjectName("mutedLabel")
        model_layout.addRow("", cuda_note)
        self.layout.addWidget(self.qwen_model_group)

        self.qwen_voice_group = QGroupBox("Voice Controls")
        voice_layout = QVBoxLayout(self.qwen_voice_group)
        self.qwen_voice_stack = QStackedWidget()
        self.qwen_voice_stack.addWidget(self._build_qwen_clone_page())
        self.qwen_voice_stack.addWidget(self._build_qwen_custom_page())
        self.qwen_voice_stack.addWidget(self._build_qwen_design_page())
        voice_layout.addWidget(self.qwen_voice_stack)
        self.layout.addWidget(self.qwen_voice_group)

        self.qwen_sampling_group = QGroupBox("Qwen Sampling")
        sampling_layout = QFormLayout(self.qwen_sampling_group)

        self.qwen_temperature_spin = QDoubleSpinBox()
        self.qwen_temperature_spin.setRange(0.1, 2.0)
        self.qwen_temperature_spin.setSingleStep(0.05)
        self.qwen_temperature_spin.setValue(0.9)
        sampling_layout.addRow("Temperature:", self.qwen_temperature_spin)

        self.qwen_top_k_spin = QSpinBox()
        self.qwen_top_k_spin.setRange(1, 200)
        self.qwen_top_k_spin.setValue(50)
        sampling_layout.addRow("Top K:", self.qwen_top_k_spin)

        self.qwen_top_p_spin = QDoubleSpinBox()
        self.qwen_top_p_spin.setRange(0.05, 1.0)
        self.qwen_top_p_spin.setSingleStep(0.05)
        self.qwen_top_p_spin.setValue(1.0)
        sampling_layout.addRow("Top P:", self.qwen_top_p_spin)

        self.qwen_repetition_spin = QDoubleSpinBox()
        self.qwen_repetition_spin.setRange(1.0, 2.0)
        self.qwen_repetition_spin.setSingleStep(0.01)
        self.qwen_repetition_spin.setValue(1.05)
        sampling_layout.addRow("Repetition:", self.qwen_repetition_spin)

        self.qwen_seed_spin = QSpinBox()
        self.qwen_seed_spin.setRange(-1, 999999)
        self.qwen_seed_spin.setValue(-1)
        sampling_layout.addRow("Seed:", self.qwen_seed_spin)

        self.qwen_do_sample_checkbox = QCheckBox("Enable sampling")
        self.qwen_do_sample_checkbox.setChecked(True)
        sampling_layout.addRow("Sampling:", self.qwen_do_sample_checkbox)
        self.layout.addWidget(self.qwen_sampling_group)

        self.qwen_performance_group = QGroupBox("Qwen Performance")
        performance_layout = QFormLayout(self.qwen_performance_group)

        self.qwen_max_tokens_spin = QSpinBox()
        self.qwen_max_tokens_spin.setRange(100, 8192)
        self.qwen_max_tokens_spin.setValue(2048)
        performance_layout.addRow("Max tokens:", self.qwen_max_tokens_spin)

        self.qwen_max_seq_spin = QSpinBox()
        self.qwen_max_seq_spin.setRange(512, 8192)
        self.qwen_max_seq_spin.setSingleStep(256)
        self.qwen_max_seq_spin.setValue(2048)
        performance_layout.addRow("Graph length:", self.qwen_max_seq_spin)

        self.qwen_streaming_checkbox = QCheckBox("Use streaming decoder internally")
        self.qwen_streaming_checkbox.setToolTip(
            "The app still returns one WAV, but Qwen decodes it in smaller pieces."
        )
        performance_layout.addRow("Streaming:", self.qwen_streaming_checkbox)

        self.qwen_stream_chunk_spin = QSpinBox()
        self.qwen_stream_chunk_spin.setRange(4, 64)
        self.qwen_stream_chunk_spin.setValue(8)
        performance_layout.addRow("Stream chunk:", self.qwen_stream_chunk_spin)
        self.qwen_streaming_checkbox.toggled.connect(self.qwen_stream_chunk_spin.setEnabled)
        self.qwen_stream_chunk_spin.setEnabled(False)
        self.layout.addWidget(self.qwen_performance_group)

    def _build_qwen_clone_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Reference audio"))
        row = QHBoxLayout()
        self.qwen_reference_input = QLineEdit()
        self.qwen_reference_input.setPlaceholderText("WAV, MP3, or FLAC reference...")
        row.addWidget(self.qwen_reference_input)
        browse = QPushButton("Browse")
        browse.setMaximumWidth(72)
        browse.clicked.connect(lambda: self._browse_audio(self.qwen_reference_input))
        row.addWidget(browse)
        layout.addLayout(row)

        layout.addWidget(QLabel("Reference transcript"))
        self.qwen_ref_text = QPlainTextEdit()
        self.qwen_ref_text.setPlaceholderText("Exact words spoken in the reference audio...")
        self.qwen_ref_text.setMaximumHeight(84)
        layout.addWidget(self.qwen_ref_text)

        self.qwen_xvec_checkbox = QCheckBox("Speaker embedding only · transcript optional")
        self.qwen_xvec_checkbox.setToolTip(
            "Better for language switching; full ICL mode usually preserves the voice more closely."
        )
        layout.addWidget(self.qwen_xvec_checkbox)

        self.qwen_append_silence_checkbox = QCheckBox("Prevent reference phoneme bleed")
        self.qwen_append_silence_checkbox.setChecked(True)
        layout.addWidget(self.qwen_append_silence_checkbox)

        layout.addWidget(QLabel("Optional style instruction"))
        self.qwen_clone_instruct = QLineEdit()
        self.qwen_clone_instruct.setPlaceholderText("e.g. Calm, intimate narration")
        layout.addWidget(self.qwen_clone_instruct)
        return page

    def _build_qwen_custom_page(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.qwen_speaker_combo = QComboBox()
        self.qwen_speaker_combo.setEditable(True)
        self.qwen_speaker_combo.addItems(
            ["Ryan", "Aiden", "Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ono_Anna", "Sohee"]
        )
        layout.addRow("Speaker:", self.qwen_speaker_combo)
        self.qwen_custom_instruct = QPlainTextEdit()
        self.qwen_custom_instruct.setPlaceholderText("Optional emotion or delivery instruction...")
        self.qwen_custom_instruct.setMaximumHeight(90)
        layout.addRow("Direction:", self.qwen_custom_instruct)
        return page

    def _build_qwen_design_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        note = QLabel("Describe the voice, accent, age, tone, and delivery you want.")
        note.setWordWrap(True)
        note.setObjectName("mutedLabel")
        layout.addWidget(note)
        self.qwen_design_instruct = QPlainTextEdit()
        self.qwen_design_instruct.setPlaceholderText(
            "A warm female audiobook narrator, soft Indian English accent, measured pace..."
        )
        self.qwen_design_instruct.setMinimumHeight(110)
        layout.addWidget(self.qwen_design_instruct)
        return page

    def _build_chunk_settings(self):
        self.chunk_group = QGroupBox("Text Chunking")
        chunk_layout = QFormLayout(self.chunk_group)
        self.split_chunks_checkbox = QCheckBox("Split long text into stable chunks")
        self.split_chunks_checkbox.setChecked(True)
        chunk_layout.addRow("Enable:", self.split_chunks_checkbox)
        self.desired_length_spin = QSpinBox()
        self.desired_length_spin.setRange(50, 500)
        self.desired_length_spin.setValue(200)
        chunk_layout.addRow("Target length:", self.desired_length_spin)
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(100, 1000)
        self.max_length_spin.setValue(300)
        chunk_layout.addRow("Maximum:", self.max_length_spin)
        self.halve_first_checkbox = QCheckBox("Use a shorter first chunk")
        chunk_layout.addRow("Warm start:", self.halve_first_checkbox)
        self.layout.addWidget(self.chunk_group)

    def _build_preset_buttons(self):
        row = QHBoxLayout()
        save = QPushButton("Save Preset")
        save.clicked.connect(self.save_as_preset)
        row.addWidget(save)
        reset = QPushButton("Reset Defaults")
        reset.clicked.connect(self.reset_to_defaults)
        row.addWidget(reset)
        self.layout.addLayout(row)

    def _on_engine_changed(self, engine_type: str):
        qwen = engine_type == "qwen3"
        for group in (
            self.chatterbox_model_group,
            self.chatterbox_voice_group,
            self.chatterbox_generation_group,
            self.chatterbox_advanced_group,
        ):
            group.setVisible(not qwen)
        for group in (
            self.qwen_model_group,
            self.qwen_voice_group,
            self.qwen_sampling_group,
            self.qwen_performance_group,
        ):
            group.setVisible(qwen)

    def _on_qwen_mode_changed(self):
        mode = self.qwen_mode_combo.currentData() or "clone"
        current_model = self.qwen_model_combo.currentData()
        self.qwen_model_combo.clear()
        for label, model_id in self.QWEN_MODELS[mode]:
            self.qwen_model_combo.addItem(label, model_id)
        index = self.qwen_model_combo.findData(current_model)
        self.qwen_model_combo.setCurrentIndex(max(0, index))
        self.qwen_voice_stack.setCurrentIndex({"clone": 0, "custom": 1, "design": 2}[mode])

    def _browse_audio(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Voice Reference", "", "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        )
        if path:
            target.setText(path)

    def browse_voice_file(self):
        self._browse_audio(self.voice_path_input)

    def get_settings(self) -> dict:
        engine_type = self.engine_selector.get_engine_type()
        qwen = engine_type == "qwen3"

        chatter_voice = self.voice_path_input.text().strip()
        if not chatter_voice:
            chatter_voice = self.voice_manager.get_selected_voice()

        mode = self.qwen_mode_combo.currentData() or "clone"
        instruct = {
            "clone": self.qwen_clone_instruct.text().strip(),
            "custom": self.qwen_custom_instruct.toPlainText().strip(),
            "design": self.qwen_design_instruct.toPlainText().strip(),
        }[mode]

        model = self.qwen_model_combo.currentData() if qwen else self.model_combo.currentText()
        voice = self.qwen_reference_input.text().strip() if qwen else chatter_voice
        temperature = self.qwen_temperature_spin.value() if qwen else self.temperature_spin.value()
        seed = self.qwen_seed_spin.value() if qwen else self.seed_spin.value()
        max_tokens = self.qwen_max_tokens_spin.value() if qwen else self.max_tokens_spin.value()

        return {
            "engine_type": engine_type,
            "api_url": self.engine_selector.get_api_url(),
            "model": model,
            "voice": voice,
            "device": "cuda" if qwen else self.device_combo.currentText(),
            "data_type": self.qwen_dtype_combo.currentText() if qwen else self.dtype_combo.currentText(),
            "use_compilation": self.compile_checkbox.isChecked(),
            "exaggeration": self.exaggeration_spin.value(),
            "cfg_weight": self.cfg_weight_spin.value(),
            "temperature": temperature,
            "seed": seed,
            "split_chunks": self.split_chunks_checkbox.isChecked(),
            "desired_length": self.desired_length_spin.value(),
            "max_length": self.max_length_spin.value(),
            "halve_first_chunk": self.halve_first_checkbox.isChecked(),
            "max_new_tokens": max_tokens,
            "cache_length": self.cache_length_spin.value(),
            "chatterbox_model": self.model_combo.currentText(),
            "chatterbox_voice": chatter_voice,
            "chatterbox_device": self.device_combo.currentText(),
            "chatterbox_data_type": self.dtype_combo.currentText(),
            "chatterbox_temperature": self.temperature_spin.value(),
            "chatterbox_seed": self.seed_spin.value(),
            "chatterbox_max_new_tokens": self.max_tokens_spin.value(),
            "qwen_mode": mode,
            "qwen_model": self.qwen_model_combo.currentData(),
            "qwen_language": self.qwen_language_combo.currentText().strip() or "Auto",
            "qwen_data_type": self.qwen_dtype_combo.currentText(),
            "qwen_reference_audio": self.qwen_reference_input.text().strip(),
            "qwen_ref_text": self.qwen_ref_text.toPlainText().strip(),
            "qwen_xvec_only": self.qwen_xvec_checkbox.isChecked(),
            "qwen_append_silence": self.qwen_append_silence_checkbox.isChecked(),
            "qwen_speaker": self.qwen_speaker_combo.currentText().strip(),
            "qwen_instruct": instruct,
            "qwen_clone_instruct": self.qwen_clone_instruct.text().strip(),
            "qwen_custom_instruct": self.qwen_custom_instruct.toPlainText().strip(),
            "qwen_design_instruct": self.qwen_design_instruct.toPlainText().strip(),
            "qwen_temperature": self.qwen_temperature_spin.value(),
            "qwen_top_k": self.qwen_top_k_spin.value(),
            "qwen_top_p": self.qwen_top_p_spin.value(),
            "qwen_repetition_penalty": self.qwen_repetition_spin.value(),
            "qwen_do_sample": self.qwen_do_sample_checkbox.isChecked(),
            "qwen_seed": self.qwen_seed_spin.value(),
            "qwen_max_new_tokens": self.qwen_max_tokens_spin.value(),
            "qwen_max_seq_len": self.qwen_max_seq_spin.value(),
            "qwen_streaming": self.qwen_streaming_checkbox.isChecked(),
            "qwen_stream_chunk_size": self.qwen_stream_chunk_spin.value(),
        }

    def apply_settings(self, settings: dict):
        engine_type = settings.get("engine_type", "local")
        self.engine_selector.set_engine_type(engine_type)
        self.engine_selector.set_api_url(settings.get("api_url", "http://localhost:7778/v1"))

        chatter_model = settings.get("chatterbox_model")
        if not chatter_model and engine_type != "qwen3":
            chatter_model = settings.get("model")
        self._set_combo_text(self.model_combo, chatter_model or "chatterbox")
        chatter_device = settings.get("chatterbox_device")
        if chatter_device is None and engine_type != "qwen3":
            chatter_device = settings.get("device", "auto")
        self._set_combo_text(self.device_combo, chatter_device or "auto")
        chatter_dtype = settings.get("chatterbox_data_type")
        if chatter_dtype is None and engine_type != "qwen3":
            chatter_dtype = settings.get("data_type", "bfloat16")
        self._set_combo_text(self.dtype_combo, chatter_dtype or "bfloat16")
        self.compile_checkbox.setChecked(bool(settings.get("use_compilation", False)))

        chatter_voice = settings.get("chatterbox_voice")
        if chatter_voice is None and engine_type != "qwen3":
            chatter_voice = settings.get("voice", "")
        self.voice_path_input.setText(chatter_voice or "")
        self.voice_manager.set_selected_voice(chatter_voice or "")

        self.exaggeration_spin.setValue(float(settings.get("exaggeration", 0.5)))
        self.cfg_weight_spin.setValue(float(settings.get("cfg_weight", 0.5)))
        self.temperature_spin.setValue(float(settings.get("chatterbox_temperature", settings.get("temperature", 0.8))))
        chatter_seed = settings.get("chatterbox_seed")
        if chatter_seed is None and engine_type != "qwen3":
            chatter_seed = settings.get("seed", -1)
        self.seed_spin.setValue(int(chatter_seed if chatter_seed is not None else -1))
        self.max_tokens_spin.setValue(int(settings.get("chatterbox_max_new_tokens", settings.get("max_new_tokens", 1000))))
        self.cache_length_spin.setValue(int(settings.get("cache_length", 1500)))

        mode = settings.get("qwen_mode", "clone")
        self._set_combo_data(self.qwen_mode_combo, mode)
        self._on_qwen_mode_changed()
        qwen_model = settings.get("qwen_model")
        if not qwen_model and engine_type == "qwen3":
            qwen_model = settings.get("model")
        self._set_combo_data(self.qwen_model_combo, qwen_model)
        self.qwen_language_combo.setCurrentText(settings.get("qwen_language", "Auto"))
        qwen_dtype = settings.get("qwen_data_type")
        if qwen_dtype is None and engine_type == "qwen3":
            qwen_dtype = settings.get("data_type", "bfloat16")
        self._set_combo_text(self.qwen_dtype_combo, qwen_dtype or "bfloat16")

        reference = settings.get("qwen_reference_audio")
        if reference is None and engine_type == "qwen3":
            reference = settings.get("voice", "")
        self.qwen_reference_input.setText(reference or "")
        self.qwen_ref_text.setPlainText(settings.get("qwen_ref_text", ""))
        self.qwen_xvec_checkbox.setChecked(bool(settings.get("qwen_xvec_only", False)))
        self.qwen_append_silence_checkbox.setChecked(bool(settings.get("qwen_append_silence", True)))
        self.qwen_speaker_combo.setCurrentText(settings.get("qwen_speaker", "Ryan"))
        self.qwen_clone_instruct.setText(settings.get("qwen_clone_instruct", ""))
        self.qwen_custom_instruct.setPlainText(settings.get("qwen_custom_instruct", ""))
        self.qwen_design_instruct.setPlainText(settings.get("qwen_design_instruct", ""))
        legacy_instruct = settings.get("qwen_instruct", "")
        if legacy_instruct:
            if mode == "clone":
                self.qwen_clone_instruct.setText(legacy_instruct)
            elif mode == "custom":
                self.qwen_custom_instruct.setPlainText(legacy_instruct)
            else:
                self.qwen_design_instruct.setPlainText(legacy_instruct)

        self.qwen_temperature_spin.setValue(float(settings.get("qwen_temperature", settings.get("temperature", 0.9))))
        self.qwen_top_k_spin.setValue(int(settings.get("qwen_top_k", 50)))
        self.qwen_top_p_spin.setValue(float(settings.get("qwen_top_p", 1.0)))
        self.qwen_repetition_spin.setValue(float(settings.get("qwen_repetition_penalty", 1.05)))
        self.qwen_do_sample_checkbox.setChecked(bool(settings.get("qwen_do_sample", True)))
        self.qwen_seed_spin.setValue(int(settings.get("qwen_seed", settings.get("seed", -1))))
        self.qwen_max_tokens_spin.setValue(int(settings.get("qwen_max_new_tokens", settings.get("max_new_tokens", 2048))))
        self.qwen_max_seq_spin.setValue(int(settings.get("qwen_max_seq_len", 2048)))
        self.qwen_streaming_checkbox.setChecked(bool(settings.get("qwen_streaming", False)))
        self.qwen_stream_chunk_spin.setValue(int(settings.get("qwen_stream_chunk_size", 8)))

        self.split_chunks_checkbox.setChecked(bool(settings.get("split_chunks", True)))
        self.desired_length_spin.setValue(int(settings.get("desired_length", 200)))
        self.max_length_spin.setValue(int(settings.get("max_length", 300)))
        self.halve_first_checkbox.setChecked(bool(settings.get("halve_first_chunk", False)))
        self._on_engine_changed(engine_type)

    def reset_to_defaults(self):
        defaults = {
            "engine_type": "local",
            "api_url": "http://localhost:7778/v1",
            "model": "chatterbox",
            "device": "auto",
            "data_type": "bfloat16",
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
            "qwen_mode": "clone",
            "qwen_model": self.QWEN_MODELS["clone"][0][1],
        }
        self.apply_settings(defaults)
        self.settings_changed.emit(defaults)

    def save_as_preset(self):
        self.settings_changed.emit(self.get_settings())

    def cleanup(self):
        self.voice_manager.cleanup()

    @staticmethod
    def _set_combo_text(combo: QComboBox, value):
        if value is None:
            return
        index = combo.findText(str(value))
        if index >= 0:
            combo.setCurrentIndex(index)
        elif combo.isEditable():
            combo.setCurrentText(str(value))

    @staticmethod
    def _set_combo_data(combo: QComboBox, value):
        if value is None:
            return
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
