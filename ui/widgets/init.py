"""
Custom widgets for the Audiobook Maker UI.
"""

from .input_tabs import InputTabsWidget
from .settings_panel import SettingsPanel
from .chunk_preview import ChunkPreviewWidget
from .preset_manager import PresetManagerDialog
from .audio_player import AudioPlayerWidget

__all__ = [
    'InputTabsWidget',
    'SettingsPanel',
    'ChunkPreviewWidget',
    'PresetManagerDialog',
    'AudioPlayerWidget'
]