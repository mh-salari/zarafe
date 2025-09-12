"""Main application window."""

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QKeyEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .core.event_manager import EventManager
from .core.gaze_data import GazeDataManager
from .core.metadata import MetadataManager
from .core.video_manager import VideoManager
from .utils.file_utils import find_video_directories, get_resource_path
from .utils.sorting import natural_sort_key
from .widgets.about_dialog import AboutDialog
from .widgets.event_controls import EventControls
from .widgets.metadata_panel import MetadataPanel
from .widgets.video_controls import VideoControls
from .widgets.video_display import VideoDisplay


class VideoAnnotator(QMainWindow):
    """Main video annotation application window."""

    def __init__(self) -> None:
        super().__init__()

        # Initialize managers
        self.video_manager = VideoManager()
        self.event_manager = EventManager()
        self.gaze_manager = GazeDataManager()
        self.metadata_manager = MetadataManager()

        # Initialize UI components
        self.video_display = VideoDisplay(self)
        self.video_controls = VideoControls(self)
        self.metadata_panel = MetadataPanel(self)
        self.event_controls = EventControls(self)

        # State
        self.video_paths: list[str] = []
        self.current_video_index = -1
        self.has_unsaved_changes = False

        self._setup_window()
        self.setup_ui()

    def _setup_window(self) -> None:
        """Configure main window."""
        self.setWindowTitle("Zarafe - Video Annotation Tool")

        icon_path = get_resource_path("app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.showMaximized()

    def setup_ui(self) -> None:
        """Initialize the user interface."""
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create panels
        left_panel = self._create_left_panel()
        center_panel = self._create_center_panel()
        right_panel = self._create_right_panel()

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([200, 600, 300])

        self.setCentralWidget(main_splitter)
        self._setup_shortcuts()

    def _create_left_panel(self) -> QWidget:
        """Create video navigation panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Directory selection
        self.open_dir_btn = QPushButton("Open Directory")
        self.open_dir_btn.clicked.connect(self.open_directory)
        layout.addWidget(self.open_dir_btn)

        # Navigation
        nav_layout = QHBoxLayout()
        self.prev_video_btn = QPushButton("Previous Video")
        self.prev_video_btn.clicked.connect(self.prev_video)
        self.next_video_btn = QPushButton("Next Video")
        self.next_video_btn.clicked.connect(self.next_video)
        nav_layout.addWidget(self.prev_video_btn)
        nav_layout.addWidget(self.next_video_btn)
        layout.addLayout(nav_layout)

        # Video list
        layout.addWidget(QLabel("Videos:"))
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.select_video)
        layout.addWidget(self.video_list)

        return panel

    def _create_center_panel(self) -> QWidget:
        """Create video display and controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Video display
        video_widget = self.video_display.setup_display()
        layout.addWidget(video_widget, 1)

        # Controls
        controls_layout = self.video_controls.setup_controls()
        layout.addLayout(controls_layout)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create metadata and event management panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Metadata
        metadata_section = self.metadata_panel.create_metadata_section()
        layout.addWidget(metadata_section)

        # Events
        event_section = self.event_controls.create_event_section()
        layout.addLayout(event_section)

        return panel

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        shortcuts = [
            ("Ctrl+Z", self.undo_action),
            ("Ctrl+S", self.save_events),
            ("Space", self.toggle_play),
            ("Right", self.next_frame),
            ("Left", self.prev_frame),
            ("Shift+Right", lambda: self.video_manager.jump_frames(10) or self.display_frame()),
            ("Shift+Left", lambda: self.video_manager.jump_frames(-10) or self.display_frame()),
        ]

        for key_sequence, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key_sequence), self)
            shortcut.activated.connect(callback)

    # Directory and video management
    def open_directory(self) -> None:
        """Open directory and scan for videos."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not dir_path:
            return

        self.video_paths.clear()
        self.video_list.clear()

        video_entries = find_video_directories(dir_path)
        video_entries.sort(key=natural_sort_key)

        for video_path, display_name in video_entries:
            self.video_paths.append(video_path)
            self.video_list.addItem(display_name)

    def select_video(self, item: QListWidgetItem) -> None:
        """Select and load video."""
        index = self.video_list.row(item)
        if 0 <= index < len(self.video_paths):
            self.load_video(index)

    def next_video(self) -> None:
        """Load next video."""
        if self.video_paths and self.current_video_index < len(self.video_paths) - 1:
            self.load_video(self.current_video_index + 1)
            self.video_list.setCurrentRow(self.current_video_index)

    def prev_video(self) -> None:
        """Load previous video."""
        if self.video_paths and self.current_video_index > 0:
            self.load_video(self.current_video_index - 1)
            self.video_list.setCurrentRow(self.current_video_index)

    def load_video(self, index: int) -> None:
        """Load video and associated data."""
        if not self.check_unsaved_changes():
            return

        self._cleanup_previous_video()

        video_path = self.video_paths[index]
        if not self.video_manager.load_video(video_path):
            self.video_label.setText(f"Error opening video: {video_path}")
            return

        self.current_video_index = index
        self._setup_video_ui()
        self._load_associated_data(Path(video_path).parent)

        self.display_frame()
        self.update_event_list()
        self.update_pupil_plot()

    def _cleanup_previous_video(self) -> None:
        """Clean up previous video state."""
        self.video_manager.release()
        self.event_manager.clear()
        self.gaze_manager.clear()
        self.has_unsaved_changes = False

    def _setup_video_ui(self) -> None:
        """Setup UI for new video."""
        self.timeline_slider.setMaximum(self.video_manager.total_frames - 1)
        self.timeline_slider.setValue(0)
        self.play_btn.setText("Play")

    def _load_associated_data(self, video_dir: Path) -> None:
        """Load gaze data, metadata, and events."""
        self.metadata_manager.set_file_name(video_dir.name)

        # Load each data type if file exists
        data_files = [
            ("gazeData.tsv", self.gaze_manager.load_gaze_data),
            ("metadata.csv", lambda p: (self.metadata_manager.load_from_csv(p), self.update_metadata_ui())),
            ("events.csv", lambda p: self.event_manager.load_from_csv(p) and self.event_manager.save_state()),
            ("markerInterval.tsv", self.event_manager.load_marker_intervals),
        ]

        for filename, loader in data_files:
            file_path = video_dir / filename
            if file_path.exists():
                try:
                    loader(file_path)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    # Playback controls
    def display_frame(self) -> None:
        """Display current frame."""
        self.video_display.render_frame()

        # Update timeline
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(self.video_manager.current_frame)
        self.timeline_slider.blockSignals(False)

    def slider_moved(self) -> None:
        """Handle timeline slider movement."""
        if self.video_manager.cap:
            self.video_manager.set_frame(self.timeline_slider.value())
            self.display_frame()

    def next_frame(self) -> None:
        """Move to next frame."""
        if self.video_manager.next_frame():
            self.display_frame()
        elif self.video_manager.playing:
            self.toggle_play()

    def prev_frame(self) -> None:
        """Move to previous frame."""
        if self.video_manager.prev_frame():
            self.display_frame()

    def toggle_play(self) -> None:
        """Toggle playback."""
        if not self.video_manager.cap:
            return

        playing = self.video_manager.toggle_playback()
        self.play_btn.setText("Pause" if playing else "Play")

        if playing:
            self.video_manager.start_playback(self.next_frame)
        else:
            self.video_manager.stop_playback()

    # Event management
    def create_event(self) -> None:
        """Create new event."""
        if not self.video_manager.cap:
            QMessageBox.warning(self, "Warning", "Please load a video first.")
            return

        selected_type = self.event_type_combo.currentText()
        if selected_type == "Select event type...":
            QMessageBox.warning(self, "Warning", "Please select an event type.")
            return

        success, message = self.event_manager.create_event(selected_type)
        if not success:
            QMessageBox.warning(self, "Event Exists", message)

        self.event_type_combo.setCurrentIndex(0)
        self.has_unsaved_changes = True
        self.update_event_list()
        self.update_pupil_plot()

    def select_event(self, item: QListWidgetItem) -> None:
        """Select event."""
        self.event_manager.select_event(self.events_list.row(item))

    def jump_to_event(self, item: QListWidgetItem) -> None:
        """Jump to event frame."""
        index = self.events_list.row(item)
        modifiers = QApplication.keyboardModifiers()
        use_end = modifiers == Qt.KeyboardModifier.ShiftModifier

        frame = self.event_manager.jump_to_event(index, use_end)
        if frame is not None:
            self.video_manager.set_frame(frame)
            self.display_frame()

    def mark_start(self) -> None:
        """Mark event start."""
        self._mark_event_frame("start", self.event_manager.mark_start)

    def mark_end(self) -> None:
        """Mark event end."""
        self._mark_event_frame("end", self.event_manager.mark_end)

    def _mark_event_frame(self, frame_type: str, mark_function) -> None:
        """Helper for marking event frames."""
        success, message = mark_function(self.video_manager.current_frame)
        if not success:
            QMessageBox.warning(self, "Warning", message)
            return

        self.has_unsaved_changes = True
        self.update_event_list()
        self.update_pupil_plot()

    def delete_event(self) -> None:
        """Delete selected event."""
        success, message = self.event_manager.delete_selected_event()
        if not success:
            QMessageBox.warning(self, "Warning", message)
            return

        self.has_unsaved_changes = True
        self.update_event_list()
        self.update_pupil_plot()

    def undo_action(self) -> None:
        """Undo last action."""
        success, _ = self.event_manager.undo()
        if success:
            self.has_unsaved_changes = len(self.event_manager.events) > 0
            self.update_event_list()
            self.update_pupil_plot()

    def save_events(self) -> None:
        """Save events to file."""
        if not self.video_manager.cap or self.current_video_index < 0:
            return

        video_dir = Path(self.video_paths[self.current_video_index]).parent
        csv_path = video_dir / "events.csv"

        success, message = self.event_manager.save_to_csv(csv_path, self.metadata_manager)
        if success:
            self.has_unsaved_changes = False
            self.event_manager.save_marker_intervals(video_dir)
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Save Failed", message)

    def update_event_list(self) -> None:
        """Update events list display."""
        self.events_list.clear()
        for i in range(len(self.event_manager.events)):
            text = self.event_manager.get_event_display_text(i)
            self.events_list.addItem(text)

        if self.event_manager.selected_event is not None:
            self.events_list.setCurrentRow(self.event_manager.selected_event)

    def update_pupil_plot(self) -> None:
        """Update pupil size visualization."""
        self.pupil_plot.update_data(
            self.gaze_manager.gaze_data, self.video_manager.total_frames, self.event_manager.events
        )

    # Metadata management
    def update_metadata(self, field: str, value: str) -> None:
        """Update metadata field."""
        self.metadata_manager.update_field(field, value)
        if self.video_manager.cap:
            self.has_unsaved_changes = True

    def update_metadata_ui(self) -> None:
        """Update metadata UI."""
        self.participant_id_input.blockSignals(True)
        self.condition_combo.blockSignals(True)
        self.series_title_input.blockSignals(True)

        self.participant_id_input.setText(self.metadata_manager.get_field("participant_id"))
        self.condition_combo.setCurrentText(self.metadata_manager.get_field("condition"))
        self.series_title_input.setText(self.metadata_manager.get_field("series_title"))

        self.participant_id_input.blockSignals(False)
        self.condition_combo.blockSignals(False)
        self.series_title_input.blockSignals(False)

    # Dialogs and utilities
    def show_about_dialog(self) -> None:
        """Show about dialog."""
        AboutDialog(self).exec()

    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes."""
        if not self.has_unsaved_changes:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save them?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_events()
            return True

        return reply != QMessageBox.StandardButton.Cancel

    # Event handlers
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key events."""
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle application close."""
        if self.check_unsaved_changes():
            self.video_manager.release()
            event.accept()
        else:
            event.ignore()
