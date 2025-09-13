"""Project selection dialog."""

from pathlib import Path

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.config import ProjectConfig
from ..utils.file_utils import find_video_directories
from .base_dialog import BaseDialog
from .new_project_dialog import NewProjectDialog

# Dialog constants
DIALOG_SIZE = (600, 500)
BUTTON_MIN_HEIGHT = 40
MAX_RECENT_PROJECTS = 10
BROWSE_TAB_INDEX = 1

# CSS styling constants
DEFAULT_LABEL_STYLE = (
    "QLabel { background-color: #1e1e1e; padding: 10px; border-radius: 4px; border: 1px solid #555555; }"
)
ERROR_LABEL_STYLE = "QLabel { background-color: #3c1e1e; color: #ffaaaa; padding: 10px; border-radius: 4px; border: 1px solid #aa5555; }"
SUCCESS_LABEL_STYLE = "QLabel { background-color: #1e2f2f; color: #aaeeff; padding: 10px; border-radius: 4px; border: 1px solid #00525f; }"


class ProjectDialog(BaseDialog):
    """Dialog for selecting and opening eye tracking projects."""

    def __init__(self, parent: object = None) -> None:
        """Initialize the project dialog."""
        super().__init__(parent, "Zarafe - Select Project", DIALOG_SIZE, True)
        self.selected_project_path = None
        self.project_config = None
        self.settings = QSettings("Zarafe", "ProjectDialog")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the project selection UI."""
        layout = self.create_main_layout()

        # Title
        title = self.create_title_label("Select Eye Tracking Project")
        layout.addWidget(title)

        # Tabs for Recent vs Browse
        self.tab_widget = QTabWidget()

        # Recent Projects Tab
        recent_tab = QWidget()
        recent_layout = QVBoxLayout(recent_tab)

        recent_desc = QLabel("Select from recently used projects:")
        recent_layout.addWidget(recent_desc)

        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.open_recent_project)
        self.recent_list.itemClicked.connect(self.select_recent_project)
        recent_layout.addWidget(self.recent_list)

        # Browse Tab
        browse_tab = QWidget()
        browse_layout = QVBoxLayout(browse_tab)

        browse_desc = QLabel("Browse for a project directory containing videos and zarafe_config.json:")
        browse_desc.setWordWrap(True)
        browse_layout.addWidget(browse_desc)

        browse_btn = QPushButton("Browse for Project Directory")
        browse_btn.clicked.connect(self.browse_project)
        browse_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        browse_layout.addWidget(browse_btn)

        # Selected path display
        self.path_label = QLabel("No project selected")
        self.path_label.setStyleSheet(DEFAULT_LABEL_STYLE)
        self.path_label.setWordWrap(True)
        browse_layout.addWidget(self.path_label)

        # Project info
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        browse_layout.addWidget(self.info_label)

        browse_layout.addStretch()

        # New Project Tab
        new_tab = QWidget()
        new_layout = QVBoxLayout(new_tab)

        new_desc = QLabel("Create a new eye tracking project with custom configuration:")
        new_desc.setWordWrap(True)
        new_layout.addWidget(new_desc)

        new_project_btn = QPushButton("Create New Project")
        new_project_btn.clicked.connect(self.create_new_project)
        new_project_btn.setMinimumHeight(BUTTON_MIN_HEIGHT)
        new_layout.addWidget(new_project_btn)

        new_layout.addStretch()

        self.tab_widget.addTab(recent_tab, "Recent Projects")
        self.tab_widget.addTab(browse_tab, "Browse")
        self.tab_widget.addTab(new_tab, "New Project")
        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout, buttons = self.create_button_layout(
            ("Cancel", self.reject),
            ("Edit Project", self.edit_project),
            ("Open Project", self.open_project),
            primary_button_idx=2,
        )
        self.edit_btn = buttons[1]
        self.open_btn = buttons[2]
        self.edit_btn.setEnabled(False)
        self.open_btn.setEnabled(False)

        layout.addLayout(button_layout)

        # Load recent projects
        self.load_recent_projects()

    def browse_project(self) -> None:
        """Browse for project directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project Directory", str(Path.home()))

        if not dir_path:
            return

        self.validate_project(Path(dir_path))

    def validate_project(self, project_path: Path) -> None:
        """Validate the selected project directory."""
        self.path_label.setText(str(project_path))

        # Check for config file
        config_path = project_path / "zarafe_config.json"
        if not config_path.exists():
            self.info_label.setText("Error: No zarafe_config.json found in this directory")
            self.path_label.setStyleSheet(ERROR_LABEL_STYLE)
            self.edit_btn.setEnabled(False)
            self.open_btn.setEnabled(False)
            return

        # Try to load config
        try:
            config = ProjectConfig(config_path)
            project_name = config.get_project_name()

            # Count videos
            video_entries = find_video_directories(str(project_path))
            video_count = len(video_entries)

            self.info_label.setText(f"Valid project: {project_name}\nFound {video_count} video recording(s)")

            # Highlight successful selection
            self.path_label.setStyleSheet(SUCCESS_LABEL_STYLE)

            self.selected_project_path = project_path
            self.project_config = config
            self.edit_btn.setEnabled(True)
            self.open_btn.setEnabled(True)

        except Exception as e:
            self.info_label.setText(f"Error: Invalid configuration file:\n{e!s}")
            self.path_label.setStyleSheet(ERROR_LABEL_STYLE)
            self.edit_btn.setEnabled(False)
            self.open_btn.setEnabled(False)

    def load_recent_projects(self) -> None:
        """Load recent projects from settings."""
        recent_projects = self.settings.value("recent_projects", [])
        if not isinstance(recent_projects, list):
            recent_projects = []

        self.recent_list.clear()

        for project_info in recent_projects:
            if isinstance(project_info, dict):
                project_path = Path(project_info.get("path", ""))
                project_name = project_info.get("name", "Unknown Project")

                if project_path.exists() and (project_path / "zarafe_config.json").exists():
                    item = QListWidgetItem(f"{project_name}\n{project_path}")
                    item.setData(Qt.ItemDataRole.UserRole, project_path)
                    self.recent_list.addItem(item)

        if self.recent_list.count() == 0:
            item = QListWidgetItem("No recent projects")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.recent_list.addItem(item)

    def select_recent_project(self, item: QListWidgetItem) -> None:
        """Select a recent project."""
        project_path = item.data(Qt.ItemDataRole.UserRole)
        if project_path:
            self.validate_project(project_path)

    def open_recent_project(self, item: QListWidgetItem) -> None:
        """Open recent project with double-click."""
        project_path = item.data(Qt.ItemDataRole.UserRole)
        if project_path:
            self.validate_project(project_path)
            if self.open_btn.isEnabled():
                self.open_project()

    def save_recent_project(self, project_path: Path, project_name: str) -> None:
        """Save project to recent projects."""
        recent_projects = self.settings.value("recent_projects", [])
        if not isinstance(recent_projects, list):
            recent_projects = []

        # Remove if already exists
        recent_projects = [p for p in recent_projects if p.get("path") != str(project_path)]

        # Add to beginning
        recent_projects.insert(0, {"path": str(project_path), "name": project_name})

        # Keep only last projects
        recent_projects = recent_projects[:MAX_RECENT_PROJECTS]

        self.settings.setValue("recent_projects", recent_projects)

    def open_project(self) -> None:
        """Open the selected project."""
        if self.selected_project_path and self.project_config:
            # Save to recent projects
            project_name = self.project_config.get_project_name()
            self.save_recent_project(self.selected_project_path, project_name)
            self.accept()
        else:
            QMessageBox.warning(self, "No Project Selected", "Please select a valid project directory first.")

    def create_new_project(self) -> None:
        """Create a new project using the NewProjectDialog."""
        new_project_dialog = NewProjectDialog(self)
        if new_project_dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the created project path
            project_path = new_project_dialog.get_project_path()
            if project_path:
                # Load and validate the newly created project
                self.validate_project(project_path)
                # Switch to browse tab to show the project info
                self.tab_widget.setCurrentIndex(BROWSE_TAB_INDEX)
                # Automatically accept to open the new project
                self.accept()

    def edit_project(self) -> None:
        """Edit the selected project configuration."""
        if self.selected_project_path:
            original_path = self.selected_project_path
            edit_dialog = NewProjectDialog(self, existing_project_path=self.selected_project_path)
            if edit_dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the potentially new project path (in case of renaming)
                new_project_path = edit_dialog.get_project_path()
                if new_project_path and new_project_path != original_path:
                    # Project was renamed - update selected path and recent projects
                    self.selected_project_path = new_project_path
                    # Update recent projects with new path
                    if hasattr(edit_dialog, "project_config"):
                        config = edit_dialog.project_config
                        project_name = config.get("project", {}).get("name", new_project_path.name)
                    else:
                        # Fallback to directory name
                        project_name = new_project_path.name
                    self.save_recent_project(new_project_path, project_name)

                # Refresh the project validation with current path
                self.validate_project(self.selected_project_path)
                # Reload recent projects to show updated list
                self.load_recent_projects()
        else:
            QMessageBox.warning(self, "No Project Selected", "Please select a project to edit.")

    def get_project_info(self) -> tuple[Path, ProjectConfig] | None:
        """Get the selected project path and config."""
        if self.selected_project_path and self.project_config:
            return self.selected_project_path, self.project_config
        return None
