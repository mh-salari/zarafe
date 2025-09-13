"""Event creation and management controls."""

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout

from ..utils.icon_loader import load_icon

# Event control constants
EVENTS_LIST_MAX_HEIGHT = 200
STRETCH_FACTOR = 1
SHORTCUTS_FONT_SIZE = 11


class EventControls:
    """Event management controls component."""

    def __init__(self, parent: object) -> None:
        """Initialize the event controls component."""
        self.parent = parent

    def create_event_section(self) -> QVBoxLayout:
        """Create the main event management section."""
        event_section = QVBoxLayout()

        # Event creation
        event_creation = self.create_event_creation()
        event_section.addLayout(event_creation)

        # Events list
        event_section.addWidget(QLabel("Events:"))
        self.parent.events_list = QListWidget()
        self.parent.events_list.setMaximumHeight(EVENTS_LIST_MAX_HEIGHT)
        self.parent.events_list.itemClicked.connect(self.parent.select_event)
        self.parent.events_list.itemDoubleClicked.connect(self.parent.jump_to_event)
        event_section.addWidget(self.parent.events_list)

        # Event controls
        event_controls = self.create_event_controls()
        event_section.addLayout(event_controls)

        # Keyboard shortcuts info
        shortcuts_section = self.create_shortcuts_info()
        event_section.addLayout(shortcuts_section)

        event_section.addStretch(STRETCH_FACTOR)

        return event_section

    def create_event_creation(self) -> QVBoxLayout:
        """Create event creation controls."""
        event_creation_layout = QVBoxLayout()
        event_creation_layout.addWidget(QLabel("Create Event:"))

        self.parent.event_type_combo = QComboBox()
        self.parent.event_type_combo.addItem("Select event type...")
        self.parent.event_type_combo.addItems(self.parent.event_manager.event_types)
        event_creation_layout.addWidget(self.parent.event_type_combo)

        self.parent.create_event_btn = QPushButton("Create Selected Event")
        self.parent.create_event_btn.clicked.connect(self.parent.create_event)
        event_creation_layout.addWidget(self.parent.create_event_btn)

        return event_creation_layout

    def create_event_controls(self) -> QVBoxLayout:
        """Create event action controls."""
        event_controls = QVBoxLayout()

        button_row1 = QHBoxLayout()
        self.parent.mark_start_btn = QPushButton("Mark Start")
        self.parent.mark_start_btn.setIcon(load_icon("mark_start", 18))
        self.parent.mark_start_btn.clicked.connect(self.parent.mark_start)
        self.parent.mark_end_btn = QPushButton("Mark End")
        self.parent.mark_end_btn.setIcon(load_icon("mark_end", 18))
        self.parent.mark_end_btn.clicked.connect(self.parent.mark_end)
        button_row1.addWidget(self.parent.mark_start_btn)
        button_row1.addWidget(self.parent.mark_end_btn)

        button_row2 = QHBoxLayout()
        self.parent.delete_event_btn = QPushButton("Delete Event")
        self.parent.delete_event_btn.setIcon(load_icon("delete", 18))
        self.parent.delete_event_btn.clicked.connect(self.parent.delete_event)
        self.parent.save_events_btn = QPushButton("Save Events")
        self.parent.save_events_btn.setIcon(load_icon("save", 18))
        self.parent.save_events_btn.clicked.connect(self.parent.save_events)
        button_row2.addWidget(self.parent.delete_event_btn)
        button_row2.addWidget(self.parent.save_events_btn)

        event_controls.addLayout(button_row1)
        event_controls.addLayout(button_row2)

        return event_controls

    @staticmethod
    def create_shortcuts_info() -> QVBoxLayout:
        """Create keyboard shortcuts information section."""
        shortcuts_layout = QVBoxLayout()

        shortcuts_label = QLabel("<h4>Keyboard Shortcuts</h4>")
        shortcuts_label.setStyleSheet("color: white")
        shortcuts_text = QLabel(
            "• <b>Space</b>: Play/Pause<br>"
            "• <b>←/→</b>: Previous/Next Frame<br>"
            "• <b>Shift+←/→</b>: Jump 10 Frames<br>"
            "• <b>M</b>: Mute/Unmute Audio<br>"
            "• <b>Ctrl+S</b>: Save Events<br>"
            "• <b>Ctrl+Z</b>: Undo"
        )
        shortcuts_text.setStyleSheet(f"color: white; font-size: {SHORTCUTS_FONT_SIZE}px;")

        shortcuts_layout.addWidget(shortcuts_label)
        shortcuts_layout.addWidget(shortcuts_text)

        return shortcuts_layout
