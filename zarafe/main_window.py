"""Main application window."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
)

from .controllers.main_controller import MainController
from .controllers.project_controller import ProjectController
from .controllers.video_navigation_controller import VideoNavigationController
from .core.config import ProjectConfig
from .core.configuration_service import ConfigurationService
from .core.event_manager import EventManager
from .core.gaze_data import GazeDataManager
from .core.shortcut_manager import ShortcutManager
from .core.video_manager import VideoManager
from .utils.file_utils import get_resource_path
from .utils.icon_loader import load_icon
from .widgets.about_dialog import AboutDialog
from .widgets.event_controls import EventControls
from .widgets.menu_manager import MenuManager
from .widgets.metadata_panel import MetadataPanel
from .widgets.panels.left_panel import LeftPanel
from .widgets.panels.main_layout_manager import MainLayoutManager
from .widgets.video_controls import VideoControls
from .widgets.video_display import VideoDisplay

# UI Constants
PANEL_SIZES = [200, 600, 300]  # Left, center, right panel widths
JUMP_FRAMES = 10  # Frame jump amount for keyboard shortcuts


class VideoAnnotator(QMainWindow):  # noqa: PLR0904
    """Main video annotation application window."""

    def __init__(self, project_path: Path | None = None, project_config: ProjectConfig | None = None) -> None:
        """Initialize the main video annotation window."""
        super().__init__()

        # Initialize configuration service
        self.config_service = ConfigurationService.get_instance()
        if project_path and project_config:
            self.config_service.load_project(project_path, project_config)

        # Initialize core managers
        self.video_manager = VideoManager()
        self.event_manager = None
        self.gaze_manager = GazeDataManager()
        self.shortcut_manager = ShortcutManager(self)

        # Initialize controllers
        self.project_controller = ProjectController()
        if project_path:
            self.project_controller.set_project_path(project_path)
        self.video_nav_controller = VideoNavigationController()
        self.main_controller = None  # Created after event_manager is initialized

        # Initialize UI managers
        self.menu_manager = MenuManager()
        self.layout_manager = MainLayoutManager(self)
        self.left_panel = LeftPanel()

        # Initialize UI components (recreated after config loads)
        self.video_display = None
        self.video_controls = None
        self.metadata_panel = None
        self.event_controls = None

        self._setup_window()
        self._connect_ui_callbacks()

        if project_config:
            self._initialize_config_components()
            self._setup_full_ui()
            self._load_project_videos()
            self.menu_manager.enable_import_videos()
            self.menu_manager.enable_project_editing()
        else:
            self._setup_basic_ui()

    def _setup_window(self) -> None:
        """Configure main window."""
        self.setWindowTitle("Zarafe - Video Annotation Tool")

        icon_path = get_resource_path("app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Setup menu bar using menu manager
        self.menu_manager.setup_menu_bar(
            self.menuBar(),
            self._show_project_dialog,
            self._edit_current_project,
            self.import_videos,
            self.show_about_dialog,
        )

        self.showMaximized()

    def _connect_ui_callbacks(self) -> None:
        """Connect UI component callbacks to controller methods."""
        self.left_panel.connect_navigation_callbacks(self.prev_video, self.next_video)
        self.left_panel.connect_video_selection_callback(self.select_video)

    def _setup_basic_ui(self) -> None:
        """Setup basic UI without config-dependent components."""
        main_widget = self.layout_manager.setup_basic_layout(self.left_panel)
        self.setCentralWidget(main_widget)
        self._setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_full_ui(self) -> None:
        """Initialize complete user interface with all components."""
        center_panel = self.layout_manager.create_center_panel(self.video_display, self.video_controls)
        right_panel = self.layout_manager.create_right_panel(self.metadata_panel, self.event_controls)

        main_widget = self.layout_manager.setup_full_layout(self.left_panel, center_panel, right_panel)
        self.setCentralWidget(main_widget)
        self._setup_shortcuts()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts using centralized manager."""
        shortcut_map = {
            "Ctrl+Z": self.undo_action,
            "Ctrl+S": self.save_events,
            "Space": self.toggle_play,
            "Right": self.next_frame,
            "Left": self.prev_frame,
            "Shift+Right": self.jump_forward_10,
            "Shift+Left": self.jump_backward_10,
            "M": self.toggle_mute,
        }

        self.shortcut_manager.register_shortcuts(shortcut_map)

    def _initialize_config_components(self) -> None:
        """Initialize components that depend on project configuration."""
        # Initialize managers with config
        self.event_manager = EventManager()

        # Initialize main controller now that event_manager exists
        self.main_controller = MainController(self.video_manager, self.event_manager, self.gaze_manager)

        # Initialize UI components with config
        self.video_display = VideoDisplay(self)
        self.video_controls = VideoControls(self)
        self.metadata_panel = MetadataPanel(self)
        self.event_controls = EventControls(self)

        # Update window title with project name
        self.setWindowTitle(f"Zarafe - {self.config_service.get_project_name()}")

    def _load_project_videos(self) -> None:
        """Load videos from the selected project directory."""
        video_paths = self.project_controller.load_project_videos(self.left_panel.video_list)
        self.video_nav_controller.set_video_paths(video_paths)

    def select_video(self, item: QListWidgetItem) -> None:
        """Select and load video using navigation controller."""
        self.video_nav_controller.select_video(item, self.left_panel.video_list, self._load_video_by_index)

    def next_video(self) -> None:
        """Navigate to next video using controller."""
        self.video_nav_controller.next_video(self._load_video_by_index)
        self.left_panel.video_list.setCurrentRow(self.video_nav_controller.get_current_index())

    def prev_video(self) -> None:
        """Navigate to previous video using controller."""
        self.video_nav_controller.prev_video(self._load_video_by_index)
        self.left_panel.video_list.setCurrentRow(self.video_nav_controller.get_current_index())

    def _load_video_by_index(self, index: int) -> None:
        """Load video by index using main controller."""
        video_paths = self.project_controller.get_video_paths()
        if self.main_controller.load_video(video_paths, index, self):
            self._setup_video_ui()
            self.display_frame()
            self.update_event_list()
            self.update_pupil_plot()

    def _setup_video_ui(self) -> None:
        """Setup UI for new video."""
        self.timeline_slider.setMaximum(self.video_manager.total_frames - 1)
        self.timeline_slider.setValue(0)
        self.play_btn.setText("Play")
        self.play_btn.setIcon(load_icon("play", 20))

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
        button_text = "Pause" if playing else "Play"
        icon_name = "pause" if playing else "play"
        self.play_btn.setText(button_text)
        self.play_btn.setIcon(load_icon(icon_name, 20))

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
        self.main_controller.mark_unsaved_changes()
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
        self._mark_event_frame(self.event_manager.mark_start)

    def mark_end(self) -> None:
        """Mark event end."""
        self._mark_event_frame(self.event_manager.mark_end)

    def _mark_event_frame(self, mark_function: object) -> None:
        """Helper for marking event frames."""
        success, message = mark_function(self.video_manager.current_frame)
        if not success:
            QMessageBox.warning(self, "Warning", message)
            return

        self.main_controller.mark_unsaved_changes()
        self.update_event_list()
        self.update_pupil_plot()

    def delete_event(self) -> None:
        """Delete selected event with confirmation."""
        if self.event_manager.selected_event is None:
            QMessageBox.warning(self, "Warning", "Please select an event to delete.")
            return

        # Get the selected event details for confirmation
        event_index = self.event_manager.selected_event
        event_text = self.event_manager.get_event_display_text(event_index)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Event",
            f"Are you sure you want to delete this event?\n\n{event_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success, message = self.event_manager.delete_selected_event()
        if not success:
            QMessageBox.warning(self, "Warning", message)
            return

        self.main_controller.mark_unsaved_changes()
        self.update_event_list()
        self.update_pupil_plot()

    def jump_forward_10(self) -> None:
        """Jump forward 10 frames."""
        self.video_manager.jump_frames(JUMP_FRAMES)
        self.display_frame()

    def jump_backward_10(self) -> None:
        """Jump backward 10 frames."""
        self.video_manager.jump_frames(-JUMP_FRAMES)
        self.display_frame()

    def toggle_mute(self) -> None:
        """Toggle audio mute/unmute."""
        is_muted = self.video_manager.audio_manager.toggle_mute()
        icon_name = "mute" if is_muted else "volume"
        self.mute_btn.setIcon(load_icon(icon_name, 20))
        self.mute_btn.setToolTip("Unmute" if is_muted else "Mute")

    def undo_action(self) -> None:
        """Undo last action."""
        success, _ = self.event_manager.undo()
        if success:
            if len(self.event_manager.events) > 0:
                self.main_controller.mark_unsaved_changes()
            self.update_event_list()
            self.update_pupil_plot()

    def save_events(self) -> None:
        """Save events to file."""
        current_index = self.video_nav_controller.get_current_index()
        if not self.video_manager.cap or current_index < 0:
            return

        video_paths = self.project_controller.get_video_paths()
        video_dir = Path(video_paths[current_index]).parent
        csv_path = video_dir / "events.csv"

        success, message = self.event_manager.save_to_csv(csv_path, self.main_controller.current_file_name)
        if success:
            self.main_controller.has_unsaved_changes = False
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

    def import_videos(self) -> None:
        """Import eye tracking recordings using project controller."""
        successfully_imported = self.project_controller.import_videos(self)

        if successfully_imported > 0:
            self._load_project_videos()
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {successfully_imported} recordings.",
            )

    def _show_project_dialog(self) -> None:
        """Show project selection dialog using project controller."""
        project_info = self.project_controller.show_project_dialog(self)
        if project_info:
            _, project_config = project_info
            self.config = project_config

            self._initialize_config_components()
            self._setup_full_ui()
            self._load_project_videos()

            self.menu_manager.enable_import_videos()
            self.menu_manager.enable_project_editing()

    def _edit_current_project(self) -> None:
        """Edit current project using project controller."""
        if self.project_controller.edit_current_project(self):
            # Reload the entire project to refresh all UI components
            self._reload_current_project()

    def _reload_current_project(self) -> None:
        """Reload the current project to refresh all UI components after changes."""
        # Update the configuration service with the potentially updated project path
        updated_project_path = self.project_controller.project_path
        if updated_project_path and self.config_service.is_project_loaded():
            # Update the project path in the configuration service
            self.config_service.update_project_path(updated_project_path)

        # Reinitialize components with updated configuration
        self._initialize_config_components()
        self._setup_full_ui()
        self._load_project_videos()

    # Dialogs and utilities
    def show_about_dialog(self) -> None:
        """Show about dialog."""
        AboutDialog(self).exec()

    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes using main controller."""
        if self.main_controller:
            return self.main_controller.check_unsaved_changes(self)
        return True

    # Event handlers
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Handle key events for shortcuts."""
        # Let QShortcut handle all shortcuts, just pass through
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle application close."""
        if self.check_unsaved_changes():
            self.video_manager.release()
            event.accept()
        else:
            event.ignore()
