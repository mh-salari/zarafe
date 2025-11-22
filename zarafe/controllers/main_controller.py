"""Main application controller for video loading and orchestration."""

from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

from ..core.event_manager import EventManager
from ..core.gaze_data import GazeDataManager
from ..core.video_manager import VideoManager


class MainController:
    """Coordinates video loading and application state management."""

    def __init__(
        self, video_manager: VideoManager, event_manager: EventManager, gaze_manager: GazeDataManager
    ) -> None:
        """Initialize the main controller with required managers."""
        self.video_manager = video_manager
        self.event_manager = event_manager
        self.gaze_manager = gaze_manager

        self.current_video_index = -1
        self.current_file_name = ""
        self.has_unsaved_changes = False

    def load_video(self, video_paths: list[str], index: int, parent_window: object) -> bool:
        """Load video and associated data files."""
        if not self.check_unsaved_changes(parent_window):
            return False

        self.cleanup_previous_video()

        video_path = Path(video_paths[index])
        if not self.video_manager.load_video(str(video_path)):
            return False

        self.current_video_index = index
        self.load_associated_data(video_path.parent)
        return True

    def cleanup_previous_video(self) -> None:
        """Clean up previous video state."""
        self.video_manager.release()
        self.event_manager.clear()
        self.gaze_manager.clear()
        self.has_unsaved_changes = False

    def load_associated_data(self, video_dir: Path) -> None:
        """Load gaze data and events."""
        self.current_file_name = video_dir.name

        # Load gaze data (checks for both gazeData.tsv and gazeData_local.tsv)
        gaze_file = video_dir / "gazeData.tsv"
        local_gaze_file = video_dir / "gazeData_local.tsv"
        if gaze_file.exists() or local_gaze_file.exists():
            try:
                self.gaze_manager.load_gaze_data(gaze_file)
            except Exception as e:
                print(f"Warning: Failed to load gaze data: {e}")

        # Load other data files
        data_files = [
            ("events.csv", lambda p: self.event_manager.load_from_csv(p) and self.event_manager.save_state()),
            ("markerInterval.tsv", self.event_manager.load_marker_intervals),
        ]

        for filename, loader in data_files:
            file_path = video_dir / filename
            if file_path.exists():
                try:
                    loader(file_path)
                except Exception as e:
                    print(f"Warning: Failed to load {filename}: {e}")

    def check_unsaved_changes(self, parent_window: object) -> bool:
        """Check if there are unsaved changes and prompt user.

        Returns:
            True if it's safe to continue (no changes, saved, or discarded)
            False if user cancelled the operation

        """
        if not self.has_unsaved_changes:
            return True

        msg_box = QMessageBox(parent_window)
        msg_box.setWindowTitle("Unsaved Changes")
        msg_box.setText("You have unsaved changes.")
        msg_box.setInformativeText("Do you want to save your changes?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Save)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Save:
            # Call the parent window's save method
            if hasattr(parent_window, "save_events"):
                parent_window.save_events()
            return True
        # Return True for Discard, False for Cancel
        return reply == QMessageBox.StandardButton.Discard

    def mark_unsaved_changes(self) -> None:
        """Mark that there are unsaved changes."""
        self.has_unsaved_changes = True
