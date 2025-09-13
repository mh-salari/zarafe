"""Base dialog class for consistent UI setup across Zarafe dialogs."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ..utils.file_utils import get_resource_path

# Dialog constants
DEFAULT_DIALOG_SIZE = (600, 500)
DEFAULT_LAYOUT_SPACING = 15
DEFAULT_LAYOUT_MARGINS = (20, 20, 20, 20)
DEFAULT_TITLE_FONT_SIZE = 16
BUTTON_MIN_HEIGHT = 40


class BaseDialog(QDialog):
    """Base class for Zarafe dialogs with consistent styling and common setup."""

    def __init__(
        self,
        parent: object = None,
        title: str = "Zarafe",
        size: tuple[int, int] = DEFAULT_DIALOG_SIZE,
        modal: bool = True,
    ) -> None:
        """Initialize the base dialog with consistent styling."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(*size)
        self.setModal(modal)

        # Set application icon
        icon_path = get_resource_path("app_icon.ico")
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
                background-color: #00525f;
                border-color: #00525f;
                font-weight: bold;
            }
            QPushButton:hover#primaryBtn {
                background-color: #007f76;
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
                selection-background-color: #00525f;
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
                background-color: #00525f;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #007f76;
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
                color: #00525f;
                font-size: 12px;
                text-decoration: underline;
                padding: 4px 8px;
                background-color: transparent;
            }
            .event-action:hover {
                color: #ffffff;
                background-color: #00525f;
                border-radius: 3px;
                text-decoration: none;
            }
        """)

    def create_main_layout(
        self, spacing: int = DEFAULT_LAYOUT_SPACING, margins: tuple[int, int, int, int] = DEFAULT_LAYOUT_MARGINS
    ) -> QVBoxLayout:
        """Create and return the main layout for the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return layout

    @staticmethod
    def create_title_label(title_text: str, font_size: int = DEFAULT_TITLE_FONT_SIZE) -> QLabel:
        """Create a styled title label."""
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(font_size)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return title

    @staticmethod
    def create_button_layout(*buttons: tuple[str, callable], primary_button_idx: int = -1) -> QHBoxLayout:
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
            btn.setMinimumHeight(BUTTON_MIN_HEIGHT)

            if i == primary_button_idx:
                btn.setObjectName("primaryBtn")

            created_buttons.append(btn)
            button_layout.addWidget(btn)

        return button_layout, created_buttons
