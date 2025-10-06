"""
Dialog to show model cache information.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QDialogButtonBox, QLabel
)
from PySide6.QtCore import Qt
from core.model_cache import ModelCacheManager


class CacheInfoDialog(QDialog):
    """Dialog showing HuggingFace model cache information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Cache Information")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📦 HuggingFace Model Cache")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Info text
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(self.font())
        layout.addWidget(self.info_text)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_cache_info)
        layout.addWidget(refresh_btn)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        # Load initial info
        self.load_cache_info()
    
    def load_cache_info(self):
        """Load and display cache information"""
        info = ModelCacheManager.get_model_info()
        
        text = f"""
<h3>Cache Directory</h3>
<p><b>Location:</b> {info['cache_directory']}</p>
<p><b>Exists:</b> {'✓ Yes' if info['cache_exists'] else '✗ No'}</p>

<h3>Cached Models ({len(info['models'])})</h3>
"""
        
        if info['models']:
            for model in info['models']:
                text += f"""
<div style="background-color: #2b2b2b; padding: 10px; margin: 5px 0; border-radius: 5px;">
    <p><b>📦 {model['name']}</b></p>
    <p style="margin-left: 20px;">
        <b>Path:</b> {model['path']}<br>
        <b>Size:</b> {model['size_mb']:.2f} MB<br>
        <b>Files:</b> {model['files']}
    </p>
</div>
"""
        else:
            text += """
<p style="color: #888;">
No Chatterbox models found in cache.<br>
Models will be downloaded automatically on first use.
</p>
"""
        
        text += """
<hr>
<h3>ℹ️ Information</h3>
<ul>
    <li>Models are stored in your HuggingFace cache directory.</li>
    <li>They are shared across all applications using HuggingFace.</li>
    <li>Safe to delete if you need space (will re-download when needed).</li>
</ul>
"""
        
        self.info_text.setHtml(text)