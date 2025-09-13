"""Main window layout coordination and panel management."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

# Layout constants
DEFAULT_PANEL_SIZES = [200, 600, 300]  # Left, center, right panel widths


class MainLayoutManager:
    """Coordinates main window layout and panel organization."""

    def __init__(self, main_window: object) -> None:
        """Initialize the main layout manager."""
        self.main_window = main_window
        self.main_splitter = None

    def setup_basic_layout(
        self, left_panel: QWidget, center_widget: QWidget = None, right_widget: QWidget = None
    ) -> QWidget:
        """Setup basic layout with placeholders for center/right panels."""
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Use provided widgets or create empty placeholders
        center_panel = center_widget or QWidget()
        right_panel = right_widget or QWidget()

        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(center_panel)
        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setSizes(DEFAULT_PANEL_SIZES)

        return self.main_splitter

    def setup_full_layout(self, left_panel: QWidget, center_panel: QWidget, right_panel: QWidget) -> QWidget:
        """Setup complete layout with all panels."""
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(center_panel)
        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setSizes(DEFAULT_PANEL_SIZES)

        return self.main_splitter

    @staticmethod
    def create_center_panel(video_display: object, video_controls: object) -> QWidget:
        """Create video display and controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Video display takes most space
        video_widget = video_display.setup_display()
        layout.addWidget(video_widget, 1)

        # Controls at bottom
        controls_layout = video_controls.setup_controls()
        layout.addLayout(controls_layout)

        return panel

    @staticmethod
    def create_right_panel(metadata_panel: object, event_controls: object) -> QWidget:
        """Create metadata and event management panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Metadata section
        metadata_section = metadata_panel.create_metadata_section()
        layout.addWidget(metadata_section)

        # Events section
        event_section = event_controls.create_event_section()
        layout.addLayout(event_section)

        return panel
