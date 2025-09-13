"""Application theming utilities."""

import os
import platform

from PyQt6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    """Apply dark theme optimized for the current platform."""
    if platform.system() == "Darwin":
        app.setProperty("apple_interfaceStyle", "dark")
        app.setStyleSheet(_get_macos_dark_stylesheet())
    elif platform.system() == "Windows":
        os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
        app.setStyle("Fusion")
        app.setStyleSheet(_get_windows_dark_stylesheet())
    else:
        app.setStyle("Fusion")
        app.setStyleSheet(_get_linux_dark_stylesheet())


def _get_macos_dark_stylesheet() -> str:
    """macOS-specific dark theme stylesheet."""
    return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QPushButton {
            background-color: transparent;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            color: #ffffff;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.08);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.12);
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
        QListWidget::item:selected {
            background-color: #00525f;
            color: white;
        }
        QListWidget::item:selected:hover {
            background-color: #007f76;
        }
        QListWidget::item:hover {
            background-color: rgba(0, 82, 95, 0.3);
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
            background-color: transparent;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            color: #ffffff;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.08);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.12);
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
        QListWidget::item:selected {
            background-color: #00525f;
            color: white;
        }
        QListWidget::item:selected:hover {
            background-color: #007f76;
        }
        QListWidget::item:hover {
            background-color: rgba(0, 82, 95, 0.3);
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
        QPushButton {
            background-color: transparent;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            color: #ffffff;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.08);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.12);
        }
    """
