"""Application theming utilities."""

import os
import platform
from PyQt6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    """Apply dark theme optimized for the current platform."""
    if platform.system() == "Darwin":
        app.setProperty("apple_interfaceStyle", "dark")
    elif platform.system() == "Windows":
        os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
        app.setStyle("Fusion")
        app.setStyleSheet(_get_windows_dark_stylesheet())
    else:
        app.setStyle("Fusion")
        app.setStyleSheet(_get_linux_dark_stylesheet())


def _get_windows_dark_stylesheet() -> str:
    """Windows-specific dark theme stylesheet."""
    return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QPushButton:pressed {
            background-color: #1e1e1e;
        }
        QLineEdit, QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 3px;
            border-radius: 3px;
        }
        QListWidget {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            alternate-background-color: #404040;
        }
        QSlider::groove:horizontal {
            background-color: #3c3c3c;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #0078d4;
            border: 1px solid #555555;
            width: 18px;
            border-radius: 9px;
            margin: -6px 0;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 3px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """


def _get_linux_dark_stylesheet() -> str:
    """Linux-specific dark theme stylesheet."""
    return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
    """
