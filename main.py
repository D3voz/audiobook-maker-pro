"""
Audiobook Maker - PySide6 Edition
A professional desktop application for converting text to audiobooks using local TTS.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """Main entry point for the application"""
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Audiobook Maker")
    app.setOrganizationName("AudiobookMaker")
    app.setApplicationVersion("2.0.0")
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()