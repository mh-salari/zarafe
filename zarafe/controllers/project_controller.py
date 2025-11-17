"""Project management controller."""

from pathlib import Path

import glassesTools.eyetracker
from PyQt6.QtWidgets import QDialog, QFileDialog, QInputDialog, QListWidget, QListWidgetItem, QMessageBox

from ..core.configuration_service import ConfigurationService
from ..utils.file_utils import find_video_directories
from ..utils.importer import import_recordings
from ..utils.sorting import natural_sort_key
from ..widgets.new_project_dialog import NewProjectDialog
from ..widgets.project_dialog import ProjectDialog


class ProjectController:
    """Manages project operations and configuration."""

    def __init__(self) -> None:
        """Initialize the project controller."""
        self.config_service = ConfigurationService.get_instance()
        self.project_path = None
        self.video_paths = []

    def show_project_dialog(self, parent_window: object) -> tuple[Path, object] | None:
        """Show project selection dialog and return project info."""
        dialog = ProjectDialog(parent_window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        project_info = dialog.get_project_info()
        if not project_info:
            return None

        project_path, project_config = project_info
        self.config_service.load_project(project_path, project_config)
        self.project_path = project_path
        return project_path, project_config

    def edit_current_project(self, parent_window: object) -> bool:
        """Edit the currently loaded project."""
        if not self.project_path:
            return False

        edit_dialog = NewProjectDialog(parent_window, existing_project_path=self.project_path)
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the updated project path (in case project was renamed)
            updated_project_path = edit_dialog.get_project_path()
            if updated_project_path:
                self.project_path = updated_project_path

            config_path = self.project_path / "zarafe_config.json"
            self.config_service.reload_config(config_path)
            return True
        return False

    def load_project_videos(self, video_list: QListWidget) -> list[str]:
        """Load all videos from the project directory."""
        if not self.project_path:
            return []

        video_dirs = find_video_directories(str(self.project_path))
        if not video_dirs:
            return []

        video_dirs.sort(key=lambda item: natural_sort_key(item[1]))

        # Extract video paths and display names from the sorted list
        self.video_paths = [video_path for video_path, _ in video_dirs]

        video_list.clear()
        for _, display_name in video_dirs:
            item = QListWidgetItem(display_name)
            video_list.addItem(item)

        return self.video_paths

    def get_video_paths(self) -> list[str]:
        """Get current video paths."""
        return self.video_paths

    def set_project_path(self, project_path: Path) -> None:
        """Set project path."""
        self.project_path = project_path

    def import_videos(self, parent_widget: object) -> int:
        """Import eye tracking recordings and return number of successfully imported recordings."""
        if not self.project_path:
            QMessageBox.warning(parent_widget, "No Project", "Please open a project first.")
            return 0

        # Create a dialog to select the eye tracker
        device_names = [d.value for d in glassesTools.eyetracker.EyeTracker if d.value.lower() != "unknown"]
        device_name, ok = QInputDialog.getItem(
            parent_widget,
            "Select Eye Tracker",
            "Select the eye tracker model:",
            device_names,
            0,
            False,
        )

        if not ok or not device_name:
            return 0

        selected_device = glassesTools.eyetracker.EyeTracker(device_name)

        # For Aria, allow selecting VRS files or directory; for others, select directory
        specific_files = None
        if selected_device.value == "Meta Aria Gen 1":
            # Ask user how they want to import
            choice, ok = QInputDialog.getItem(
                parent_widget,
                "Aria Import Method",
                "How would you like to import?",
                ["Select specific VRS file(s)", "Import all from directory"],
                0,
                False,
            )
            if not ok:
                return 0

            if choice == "Select specific VRS file(s)":
                # Select specific VRS files
                vrs_files, _ = QFileDialog.getOpenFileNames(
                    parent_widget, "Select Aria VRS Recording(s)", str(Path.home()), "VRS Files (*.vrs);;All Files (*)"
                )
                if not vrs_files:
                    return 0

                # Convert to Path objects
                specific_files = [Path(f) for f in vrs_files]
                # Use the parent directory of the first VRS file as source_dir
                source_dir = specific_files[0].parent
            else:
                # Import all from directory
                source_dir_str = QFileDialog.getExistingDirectory(
                    parent_widget, "Select Directory Containing VRS Files", str(Path.home())
                )
                if not source_dir_str:
                    return 0
                source_dir = Path(source_dir_str)
        else:
            source_dir_str = QFileDialog.getExistingDirectory(
                parent_widget, "Select Eye Tracker Recording Directory", str(Path.home())
            )
            if not source_dir_str:
                return 0
            source_dir = Path(source_dir_str)

        successfully_imported = import_recordings(
            source_dir=source_dir,
            project_path=self.project_path,
            device=selected_device,
            parent_widget=parent_widget,
            specific_files=specific_files,
        )

        return successfully_imported
