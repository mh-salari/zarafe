"""New project creation dialog."""

import json
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QGroupBox,
    QColorDialog,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QWidget,
)

from ..utils.file_utils import get_resource_path


class NewProjectDialog(QDialog):
    """Dialog for creating new eye tracking projects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_config = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the new project creation UI."""
        self.setWindowTitle("Zarafe - Create New Project")
        self.setFixedSize(700, 600)
        self.setModal(False)

        # Set application icon
        icon_path = get_resource_path("app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Apply dark theme styles
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton#createBtn {
                background-color: #4CAF50;
                border-color: #4CAF50;
                font-weight: bold;
            }
            QPushButton:hover#createBtn {
                background-color: #45a049;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                padding: 6px;
                border-radius: 4px;
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
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #555555;
            }
            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Create New Eye Tracking Project")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scrollable content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Project Info
        project_group = QGroupBox("Project Information")
        project_form = QFormLayout(project_group)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("e.g., Museum Eye Tracking Study")
        project_form.addRow("Project Name:", self.project_name_input)

        scroll_layout.addWidget(project_group)

        # Event Types
        events_group = QGroupBox("Event Types")
        events_layout = QVBoxLayout(events_group)

        events_desc = QLabel("Define what behaviors/events you want to time-annotate in your videos")
        events_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        events_layout.addWidget(events_desc)

        # Event creation buttons
        event_btn_layout = QHBoxLayout()

        glasses_btn = QPushButton("Add Accuracy Test (glassesValidator)")
        glasses_btn.clicked.connect(self.add_glasses_validator_event)
        event_btn_layout.addWidget(glasses_btn)

        custom_btn = QPushButton("Add Custom Event")
        custom_btn.clicked.connect(self.add_custom_event)
        event_btn_layout.addWidget(custom_btn)

        events_layout.addLayout(event_btn_layout)

        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(100)
        events_layout.addWidget(self.events_list)

        scroll_layout.addWidget(events_group)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()

        self.create_btn = QPushButton("Create Project Configuration")
        self.create_btn.setObjectName("createBtn")
        self.create_btn.clicked.connect(self.create_project)
        self.create_btn.setMinimumHeight(40)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setMinimumHeight(40)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

    def add_glasses_validator_event(self) -> None:
        """Add glassesValidator accuracy test event."""
        # Check if accuracy test already exists
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            event_data = item.data(Qt.ItemDataRole.UserRole)
            if event_data.get("applies_to") == "glassesValidator":
                QMessageBox.warning(self, "Duplicate Event", "Only one Accuracy Test event is allowed.")
                return

        # Open color dialog
        color = QColorDialog.getColor()
        if color.isValid():
            rgb = [color.red(), color.green(), color.blue()]
            self._add_event_to_list("Accuracy Test", rgb, "glassesValidator")

    def add_custom_event(self) -> None:
        """Add a custom event with color selection."""
        from PyQt6.QtWidgets import QInputDialog

        event_name, ok = QInputDialog.getText(self, "Custom Event", "Enter event name:")
        if ok and event_name.strip():
            # Open color dialog
            color = QColorDialog.getColor()
            if color.isValid():
                rgb = [color.red(), color.green(), color.blue()]
                self._add_event_to_list(event_name.strip(), rgb)

    def _add_event_to_list(self, name: str, rgb: list, applies_to: str = None) -> None:
        """Add event to list with colored box and delete button."""
        # Create custom widget for the list item
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 2, 5, 2)

        # Color box
        color_box = QLabel()
        color_box.setFixedSize(20, 20)
        color_box.setStyleSheet(f"background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border: 1px solid #555;")
        item_layout.addWidget(color_box)

        # Event name (clickable for rename)
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; padding-left: 5px;")
        name_label.mousePressEvent = (
            lambda event: self._rename_event(item, name_label) if event.button() == Qt.MouseButton.LeftButton else None
        )
        item_layout.addWidget(name_label)

        item_layout.addStretch()

        # Delete link
        delete_label = QLabel("delete")
        delete_label.setStyleSheet("color: #cccccc;")
        delete_label.mousePressEvent = lambda event: self._delete_event_item(item)
        item_layout.addWidget(delete_label)

        # Create list item and set custom widget
        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())

        # Store event data
        event_data = {"name": name, "color": rgb}
        if applies_to:
            event_data["applies_to"] = applies_to
        item.setData(Qt.ItemDataRole.UserRole, event_data)

        self.events_list.addItem(item)
        self.events_list.setItemWidget(item, item_widget)

    def _rename_event(self, item: QListWidgetItem, name_label: QLabel) -> None:
        """Rename an event by clicking on its name."""
        event_data = item.data(Qt.ItemDataRole.UserRole)

        # Don't allow renaming accuracy test
        if event_data.get("applies_to") == "glassesValidator":
            QMessageBox.information(self, "Cannot Rename", "Accuracy Test name cannot be changed.")
            return

        from PyQt6.QtWidgets import QInputDialog

        current_name = event_data["name"]
        new_name, ok = QInputDialog.getText(self, "Rename Event", "Enter new name:", text=current_name)

        if ok and new_name.strip() and new_name.strip() != current_name:
            # Update the event data
            event_data["name"] = new_name.strip()
            item.setData(Qt.ItemDataRole.UserRole, event_data)
            # Update the label
            name_label.setText(new_name.strip())

    def _delete_event_item(self, item: QListWidgetItem) -> None:
        """Delete an event item from the list."""
        row = self.events_list.row(item)
        self.events_list.takeItem(row)

    def create_project(self) -> None:
        """Create or update the project configuration."""
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter a project name.")
            return

        if self.events_list.count() == 0:
            QMessageBox.warning(self, "Missing Information", "Please add at least one event type.")
            return

        # If editing, use existing project path
        if hasattr(self.parent(), "project_path") and self.parent().project_path:
            project_path = self.parent().project_path
        else:
            # Ask where to create the project
            parent_dir = QFileDialog.getExistingDirectory(self, "Select Parent Directory for New Project")
            if not parent_dir:
                return

            # Create project directory
            project_name = self.project_name_input.text().strip()
            safe_project_name = project_name.replace(" ", "_").replace("/", "_")
            project_path = Path(parent_dir) / safe_project_name

            try:
                project_path.mkdir(exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Directory Error", f"Failed to create project directory:\n{str(e)}")
                return

        # Build configuration
        config = {
            "project": {"name": self.project_name_input.text().strip()},
            "event_types": [],
            "default_color": [123, 171, 61],
        }

        # Add event types
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            event_data = item.data(Qt.ItemDataRole.UserRole)
            config["event_types"].append(event_data)

        # Save configuration
        config_path = project_path / "zarafe_config.json"
        try:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "Project Created",
                f"Project directory created at:\n{project_path}\n\n"
                "You can now add video files to this directory and open the project in Zarafe.",
            )

            self.project_path = project_path
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project configuration:\n{str(e)}")

    def get_project_path(self) -> Path | None:
        """Get the created project path."""
        return getattr(self, "project_path", None)
