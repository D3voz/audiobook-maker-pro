"""
Audio player widget with playback controls and seeking.
"""

import os
import tempfile
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle
)
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayerWidget(QWidget):
    """
    Audio player widget with play/pause/stop controls and seekable timeline.
    """
    
    def __init__(self):
        super().__init__()
        
        # Media player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Temporary file for current audio
        self.temp_audio_file = None
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        
        # Initially disabled
        self.setEnabled(False)
    
    def setup_ui(self):
        """Setup the player UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Timeline slider
        timeline_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setMinimumWidth(45)
        timeline_layout.addWidget(self.current_time_label)
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.sliderMoved.connect(self.seek)
        self.timeline_slider.setToolTip("Drag to seek through audio")
        timeline_layout.addWidget(self.timeline_slider)
        
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setMinimumWidth(45)
        self.total_time_label.setAlignment(Qt.AlignRight)
        timeline_layout.addWidget(self.total_time_label)
        
        layout.addLayout(timeline_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("▶️ Play")
        self.play_pause_btn.setMinimumWidth(100)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_btn)
        
        # Skip backward button
        self.skip_back_btn = QPushButton("⏪ -10s")
        self.skip_back_btn.clicked.connect(self.skip_backward)
        self.skip_back_btn.setToolTip("Skip backward 10 seconds")
        controls_layout.addWidget(self.skip_back_btn)
        
        # Skip forward button
        self.skip_forward_btn = QPushButton("⏩ +10s")
        self.skip_forward_btn.clicked.connect(self.skip_forward)
        self.skip_forward_btn.setToolTip("Skip forward 10 seconds")
        controls_layout.addWidget(self.skip_forward_btn)
        
        # Volume slider
        volume_label = QLabel("🔊")
        controls_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setToolTip("Adjust volume")
        controls_layout.addWidget(self.volume_slider)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Set initial volume
        self.set_volume(70)
    
    def load_audio(self, audio_data: bytes):
        """
        Load audio data into the player.
        
        Args:
            audio_data: Audio file data (WAV format)
        """
        # Stop current playback
        self.stop()
        
        # Clean up old temp file
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass
        
        # Create temporary file
        fd, self.temp_audio_file = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        
        # Write audio data to temp file
        with open(self.temp_audio_file, 'wb') as f:
            f.write(audio_data)
        
        # Load into player
        self.player.setSource(QUrl.fromLocalFile(self.temp_audio_file))
        
        # Enable player
        self.setEnabled(True)
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Start playback"""
        self.player.play()
    
    def pause(self):
        """Pause playback"""
        self.player.pause()
    
    def stop(self):
        """Stop playback and reset to beginning"""
        self.player.stop()
    
    def seek(self, position):
        """
        Seek to a specific position.
        
        Args:
            position: Position in milliseconds
        """
        self.player.setPosition(position)
    
    def skip_backward(self):
        """Skip backward 10 seconds"""
        new_position = max(0, self.player.position() - 10000)
        self.player.setPosition(new_position)
    
    def skip_forward(self):
        """Skip forward 10 seconds"""
        new_position = min(self.player.duration(), self.player.position() + 10000)
        self.player.setPosition(new_position)
    
    def set_volume(self, volume):
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0-100)
        """
        self.audio_output.setVolume(volume / 100.0)
    
    @Slot(int)
    def on_position_changed(self, position):
        """Update UI when playback position changes"""
        # Update slider (but not if user is dragging it)
        if not self.timeline_slider.isSliderDown():
            self.timeline_slider.setValue(position)
        
        # Update time label
        self.current_time_label.setText(self.format_time(position))
    
    @Slot(int)
    def on_duration_changed(self, duration):
        """Update UI when duration is known"""
        self.timeline_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))
    
    @Slot(QMediaPlayer.PlaybackState)
    def on_state_changed(self, state):
        """Update button states based on playback state"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸ Pause")
        else:
            self.play_pause_btn.setText("▶️ Play")
    
    def format_time(self, ms):
        """
        Format milliseconds as MM:SS.
        
        Args:
            ms: Time in milliseconds
            
        Returns:
            Formatted time string
        """
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def clear(self):
        """Clear the player and disable controls"""
        self.stop()
        self.player.setSource(QUrl())
        self.setEnabled(False)
        
        # Clean up temp file
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass
            self.temp_audio_file = None
    
    def cleanup(self):
        """Cleanup resources (call on app close)"""
        self.clear()