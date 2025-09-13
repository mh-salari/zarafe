"""Left navigation panel for video management."""

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LeftPanel(QWidget):
    """Video navigation and management panel."""

    def __init__(self) -> None:
        """Initialize the left panel."""
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initialize the panel layout and widgets."""
        layout = QVBoxLayout(self)

        # Import videos section
        self.import_videos_btn = QPushButton("Import Videos")
        self.import_videos_btn.hide()  # Hidden until project loads
        layout.addWidget(self.import_videos_btn)

        # Navigation controls
        nav_layout = QHBoxLayout()
        self.prev_video_btn = QPushButton("Previous Video")
        self.next_video_btn = QPushButton("Next Video")
        nav_layout.addWidget(self.prev_video_btn)
        nav_layout.addWidget(self.next_video_btn)
        layout.addLayout(nav_layout)

        # Video list section
        layout.addWidget(QLabel("Videos:"))
        self.video_list = QListWidget()
        layout.addWidget(self.video_list)

    def _connect_signals(self) -> None:
        """Connect internal widget signals."""
        # Signals will be connected to external controllers by the main window

    def connect_import_callback(self, callback: object) -> None:
        """Connect import videos callback."""
        self.import_videos_btn.clicked.connect(callback)

    def connect_navigation_callbacks(self, prev_callback: object, next_callback: object) -> None:
        """Connect video navigation callbacks."""
        self.prev_video_btn.clicked.connect(prev_callback)
        self.next_video_btn.clicked.connect(next_callback)

    def connect_video_selection_callback(self, callback: object) -> None:
        """Connect video selection callback."""
        self.video_list.itemClicked.connect(callback)

    def show_import_button(self) -> None:
        """Show import videos button when project is loaded."""
        self.import_videos_btn.show()

    def hide_import_button(self) -> None:
        """Hide import videos button."""
        self.import_videos_btn.hide()
