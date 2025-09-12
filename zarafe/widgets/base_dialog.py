"""Base dialog class for consistent UI setup across Zarafe dialogs."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


from ..utils.file_utils import get_resource_path


class BaseDialog(QDialog):
    """Base class for Zarafe dialogs with consistent styling and common setup."""

    def __init__(self, parent=None, title: str = "Zarafe", size: tuple[int, int] = (600, 500), modal: bool = True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(*size)
        self.setModal(modal)

        # Set application icon
        icon_path = get_resource_path("app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Apply consistent dark theme
        self._apply_dark_theme()

    def _apply_dark_theme(self) -> None:
        """Apply consistent dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton:enabled#primaryBtn {
                background-color: #4CAF50;
                border-color: #4CAF50;
                font-weight: bold;
            }
            QPushButton:hover#primaryBtn {
                background-color: #45a049;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #555555;
                color: #ffffff;
                background-color: #3c3c3c;
                font-size: 13px;
                min-height: 40px;
                margin: 1px;
                border-radius: 4px;
            }
            QListWidget::item:alternate {
                background-color: #353535;
            }
            QListWidget::item:hover {
                background-color: #4c4c4c;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #45a049;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #555555;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
                border-bottom: 1px solid #3c3c3c;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }
            /* Event list item styling for better visibility */
            .event-name {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding-left: 8px;
                background-color: transparent;
            }
            .event-action {
                color: #4CAF50;
                font-size: 12px;
                text-decoration: underline;
                padding: 4px 8px;
                background-color: transparent;
            }
            .event-action:hover {
                color: #ffffff;
                background-color: #4CAF50;
                border-radius: 3px;
                text-decoration: none;
            }
        """)

    def create_main_layout(
        self, spacing: int = 15, margins: tuple[int, int, int, int] = (20, 20, 20, 20)
    ) -> QVBoxLayout:
        """Create and return the main layout for the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return layout

    def create_title_label(self, title_text: str, font_size: int = 16) -> QLabel:
        """Create a styled title label."""
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(font_size)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return title

    def create_button_layout(self, *buttons: tuple[str, callable], primary_button_idx: int = -1) -> QHBoxLayout:
        """Create a button layout with consistent styling.

        Args:
            buttons: Tuples of (button_text, callback_function)
            primary_button_idx: Index of the primary button (gets special styling)

        Returns:
            QHBoxLayout with the configured buttons
        """
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        created_buttons = []
        for i, (text, callback) in enumerate(buttons):
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(40)

            if i == primary_button_idx:
                btn.setObjectName("primaryBtn")

            created_buttons.append(btn)
            button_layout.addWidget(btn)

        return button_layout, created_buttons
