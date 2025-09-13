"""New project creation dialog."""

import csv
import json
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWidgets import QLabel as DialogLabel

from ..utils.icon_loader import load_icon
from .base_dialog import BaseDialog


class HoverActionWidget(QWidget):
    """Custom widget for actions with hover effects."""

    def __init__(
        self,
        icon_name: str,
        text: str,
        callback: Callable[[], None],
        hover_color: str = "#f44336",
        parent: QWidget | None = None,
    ) -> None:
        """Initialize hover action widget."""
        super().__init__(parent)
        self.callback = callback
        self.icon_name = icon_name
        self.text = text
        self.hover_color = hover_color
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 8, 4)
        layout.setSpacing(4)

        # Create icon and text
        self.icon_label = QLabel()
        self.icon_label.setPixmap(load_icon(self.icon_name, 14).pixmap(14, 14))
        self.text_label = QLabel(self.text)
        self.text_label.setStyleSheet("color: #ffffff; font-size: 12px;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        """Change to hover color on hover."""
        self.icon_label.setPixmap(load_icon(self.icon_name, 14, self.hover_color).pixmap(14, 14))
        self.text_label.setStyleSheet(f"color: {self.hover_color}; font-size: 12px;")
        super().enterEvent(event)

    def leaveEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        """Change back to white when not hovering."""
        self.icon_label.setPixmap(load_icon(self.icon_name, 14).pixmap(14, 14))
        self.text_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Handle mouse click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class NewProjectDialog(BaseDialog):
    """Dialog for creating new eye tracking projects."""

    def __init__(self, parent: object = None, existing_project_path: Path | None = None) -> None:
        """Initialize the new project dialog."""
        # Set existing_project_path FIRST before calling super().__init__
        self.existing_project_path = existing_project_path

        title = "Zarafe - Edit Project" if existing_project_path else "Zarafe - Create New Project"
        super().__init__(parent, title, (700, 600), False)
        self.project_config = {}
        self.original_event_names = []  # Track original event names for rename detection
        self.setup_ui()

        # Load existing project data if editing
        if self.existing_project_path:
            self._load_existing_project()

    def setup_ui(self) -> None:  # noqa: PLR0914
        """Setup the new project creation UI."""
        layout = self.create_main_layout()

        # Title - dynamic based on create vs edit mode
        title_text = "Edit Eye Tracking Project" if self.existing_project_path else "Create New Eye Tracking Project"
        title = self.create_title_label(title_text)
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
        events_desc.setStyleSheet("color: #ffffff; font-size: 12px; background-color: transparent;")
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
        self.events_list.setMaximumHeight(200)
        self.events_list.setMinimumHeight(120)
        # Enable alternating row colors for better visibility
        self.events_list.setAlternatingRowColors(True)
        events_layout.addWidget(self.events_list)

        scroll_layout.addWidget(events_group)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Buttons - text depends on create vs edit mode
        button_text = "Save" if self.existing_project_path else "Create Project Configuration"
        button_layout, buttons = self.create_button_layout(
            ("Cancel", self.close), (button_text, self.save_project), primary_button_idx=1
        )
        self.save_btn = buttons[1]

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
        """Add a custom event using the same dialog as edit."""
        # Use the same edit dialog but with empty initial values
        self._edit_or_add_event()

    def _add_event_to_list(self, name: str, rgb: list, applies_to: str | None = None) -> None:
        """Add event to list with colored box and action buttons."""
        # Create custom widget for the list item
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(8, 4, 8, 4)

        # Color box (clickable to change color)
        color_box = QLabel()
        color_box.setFixedSize(24, 24)
        color_box.setStyleSheet(
            f"background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border: 2px solid #ffffff; border-radius: 4px;"
        )
        color_box.setCursor(Qt.CursorShape.PointingHandCursor)
        color_box.mousePressEvent = lambda _: self._edit_or_add_event(item, name_label, color_box)
        item_layout.addWidget(color_box)

        # Event name
        name_label = QLabel(name)
        name_label.setStyleSheet(
            "color: #ffffff; font-weight: bold; font-size: 14px; padding-left: 8px; background-color: transparent;"
        )
        item_layout.addWidget(name_label)

        item_layout.addStretch()

        # Event name is clickable for rename (except Accuracy Test)
        can_rename = applies_to != "glassesValidator"
        if can_rename:
            name_label.setCursor(Qt.CursorShape.PointingHandCursor)
            name_label.mousePressEvent = (
                lambda event: self._edit_event(item, name_label, color_box)
                if event.button() == Qt.MouseButton.LeftButton
                else None
            )

        # Edit action with teal hover effect
        edit_widget = HoverActionWidget(
            "edit", "edit", lambda: self._edit_or_add_event(item, name_label, color_box), hover_color="#00525f"
        )
        item_layout.addWidget(edit_widget)

        # Delete action with red hover effect
        delete_widget = HoverActionWidget(
            "delete", "delete", lambda: self._delete_event_item(item), hover_color="#f44336"
        )
        item_layout.addWidget(delete_widget)

        # Create list item - let CSS handle the styling
        item = QListWidgetItem()

        # Store event data
        event_data = {"name": name, "color": rgb}
        if applies_to:
            event_data["applies_to"] = applies_to
        item.setData(Qt.ItemDataRole.UserRole, event_data)

        self.events_list.addItem(item)
        self.events_list.setItemWidget(item, item_widget)

    def _edit_or_add_event(  # noqa: PLR0914
        self, item: QListWidgetItem = None, name_label: QLabel = None, color_box: QLabel = None
    ) -> None:
        """Single dialog for both editing existing events and adding new ones."""
        # Determine if this is edit (has item) or add (no item)
        is_editing = item is not None

        if is_editing:
            event_data = item.data(Qt.ItemDataRole.UserRole)
            current_name = event_data["name"]
            current_color = event_data["color"]
            can_rename = event_data.get("applies_to") != "glassesValidator"
        else:
            # Adding new event - start with defaults
            current_name = ""
            current_color = [123, 171, 61]  # Default green
            can_rename = True

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Event")
        dialog.setModal(True)
        dialog.setFixedSize(400, 160)
        dialog.setStyleSheet(self.styleSheet())  # Same dark theme

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name field (always shown, disabled for Accuracy Test)
        name_layout = QHBoxLayout()
        name_layout.addWidget(DialogLabel("Name:"))
        name_input = QLineEdit(current_name)
        if not can_rename:
            name_input.setEnabled(False)
            name_input.setStyleSheet("background-color: #2a2a2a; color: #888888;")
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        # Color selection (always shown and editable)
        color_layout = QHBoxLayout()
        color_layout.addWidget(DialogLabel("Color:"))

        self.selected_color = current_color.copy()
        color_preview = DialogLabel("      ")
        color_preview.setFixedSize(50, 25)
        color_preview.setStyleSheet(
            f"background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]}); border: 2px solid #ffffff; border-radius: 4px;"
        )
        color_layout.addWidget(color_preview)

        color_btn = QPushButton("Choose Color")
        color_btn.clicked.connect(lambda: self._select_color_in_dialog(color_preview))
        color_layout.addWidget(color_btn)
        layout.addLayout(color_layout)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(dialog.accept)
        save_btn.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if is_editing:
                # Update existing event
                if can_rename and name_input.text().strip() != current_name:
                    event_data["name"] = name_input.text().strip()
                    name_label.setText(name_input.text().strip())

                if self.selected_color != current_color:
                    event_data["color"] = self.selected_color
                    color_box.setStyleSheet(
                        f"background-color: rgb({self.selected_color[0]}, {self.selected_color[1]}, {self.selected_color[2]}); border: 2px solid #ffffff; border-radius: 4px;"
                    )

                item.setData(Qt.ItemDataRole.UserRole, event_data)
            else:
                # Add new event
                new_name = name_input.text().strip()
                if new_name:  # Only add if name is not empty
                    self._add_event_to_list(new_name, self.selected_color)

    def _select_color_in_dialog(self, color_preview: QLabel) -> None:
        """Select color and update preview in the same dialog."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = [color.red(), color.green(), color.blue()]
            color_preview.setStyleSheet(
                f"background-color: rgb({self.selected_color[0]}, {self.selected_color[1]}, {self.selected_color[2]}); border: 2px solid #ffffff; border-radius: 4px;"
            )

    def _delete_event_item(self, item: QListWidgetItem) -> None:
        """Delete an event item from the list with confirmation."""
        # Get event name for confirmation
        widget = self.events_list.itemWidget(item)
        event_name = "this event"
        if widget:
            # Try to find the event name from the widget
            for child in widget.findChildren(QLabel):
                if child.text() and not child.text().startswith(" ") and child.text() not in {"edit", "delete"}:
                    event_name = f'"{child.text()}"'
                    break

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Event",
            f"Are you sure you want to delete {event_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = self.events_list.row(item)
            self.events_list.takeItem(row)

    def save_project(self) -> None:
        """Save or update the project configuration."""
        if not self._validate_inputs():
            return

        project_path = self._get_or_create_project_path()
        if not project_path:
            return

        config = self._build_project_config()
        if not self._save_config_file(project_path, config):
            return

        self._handle_post_save_actions(project_path, config)

    def _validate_inputs(self) -> bool:
        """Validate user inputs before saving."""
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter a project name.")
            return False

        if self.events_list.count() == 0:
            QMessageBox.warning(self, "Missing Information", "Please add at least one event type.")
            return False

        return True

    def _get_or_create_project_path(self) -> Path | None:
        """Get project path for editing or create new project directory."""
        if self.existing_project_path:
            return self._handle_existing_project_path()
        return self._create_new_project_path()

    def _handle_existing_project_path(self) -> Path:
        """Handle project path for editing, including potential renaming."""
        project_path = self.existing_project_path
        old_project_name = project_path.name
        new_project_name = self.project_name_input.text().strip().replace(" ", "_").replace("/", "_")

        if old_project_name != new_project_name:
            new_project_path = project_path.parent / new_project_name
            try:
                project_path.rename(new_project_path)
                project_path = new_project_path
            except Exception as e:
                QMessageBox.warning(self, "Rename Error", f"Could not rename project directory:\n{e!s}")

        return project_path

    def _create_new_project_path(self) -> Path | None:
        """Create new project directory."""
        parent_dir = QFileDialog.getExistingDirectory(self, "Select Parent Directory for New Project")
        if not parent_dir:
            return None

        project_name = self.project_name_input.text().strip()
        safe_project_name = project_name.replace(" ", "_").replace("/", "_")
        project_path = Path(parent_dir) / safe_project_name

        try:
            project_path.mkdir(exist_ok=True)
            return project_path
        except Exception as e:
            QMessageBox.critical(self, "Directory Error", f"Failed to create project directory:\n{e!s}")
            return None

    def _build_project_config(self) -> dict:
        """Build project configuration dictionary."""
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

        return config

    def _save_config_file(self, project_path: Path, config: dict) -> bool:
        """Save configuration to file."""
        config_path = project_path / "zarafe_config.json"
        try:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project configuration:\n{e!s}")
            return False

    def _handle_post_save_actions(self, project_path: Path, config: dict) -> None:
        """Handle actions after successful save."""
        if self.existing_project_path:
            self._handle_edit_completion(project_path, config)
        else:
            self._handle_creation_completion(project_path)

    def _handle_edit_completion(self, project_path: Path, config: dict) -> None:
        """Handle completion of project editing."""
        original_config = self.project_config if hasattr(self, "project_config") else {}

        if original_config and self._config_affects_csv_data(original_config, config):
            actions_info = self._get_csv_update_actions(original_config, config)
            if self._confirm_csv_update(actions_info):
                self._update_existing_csv_files(project_path, original_config, config)

        self.project_path = project_path
        self.accept()

    def _handle_creation_completion(self, project_path: Path) -> None:
        """Handle completion of project creation."""
        QMessageBox.information(
            self,
            "Project Created",
            f"Project created successfully at:\n{project_path}\n\n"
            "You can now add video files to this directory and open the project in Zarafe.",
        )
        self.project_path = project_path
        self.accept()

    def get_project_path(self) -> Path | None:
        """Get the created project path."""
        return getattr(self, "project_path", None)

    def _load_existing_project(self) -> None:
        """Load existing project configuration for editing."""
        try:
            config_path = self.existing_project_path / "zarafe_config.json"
            if config_path.exists():
                with config_path.open("r", encoding="utf-8") as f:
                    config = json.load(f)

                # Store config for later use
                self.project_config = config

                # Load project name
                project_name = config.get("project", {}).get("name", "")
                self.project_name_input.setText(project_name)

                # Load event types and track original names
                event_types = config.get("event_types", [])
                for event_type in event_types:
                    name = event_type.get("name", "")
                    color = event_type.get("color", [123, 171, 61])
                    applies_to = event_type.get("applies_to")
                    if name:
                        self.original_event_names.append(name)  # Track original names
                        self._add_event_to_list(name, color, applies_to)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load project configuration:\n{e!s}")

    def _analyze_event_changes(self) -> tuple[dict, list, list]:
        """Analyze what operations were performed on events.

        Returns:
            (renames_dict, deleted_list, added_list)

        """
        # Get current event names from the UI list
        current_events = []
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            event_data = item.data(Qt.ItemDataRole.UserRole)
            current_events.append(event_data["name"])

        # Find potential renames by matching list positions FIRST
        renames = {}
        if len(self.original_event_names) == len(current_events):
            # Same count - check for positional renames
            renames = {
                orig_name: curr_name
                for orig_name, curr_name in zip(self.original_event_names, current_events, strict=False)
                if orig_name != curr_name
            }

        # Now find what's truly deleted and added (after accounting for renames)
        original_set = set(self.original_event_names)
        current_set = set(current_events)

        # Remove renamed items from the sets
        for old_name, new_name in renames.items():
            original_set.discard(old_name)
            current_set.discard(new_name)

        deleted = list(original_set - current_set)
        added = list(current_set - original_set)

        return renames, deleted, added

    @staticmethod
    def _config_affects_csv_data(old_config: dict, new_config: dict) -> bool:
        """Check if config changes affect existing CSV data."""
        old_event_types = old_config.get("event_types", [])
        new_event_types = new_config.get("event_types", [])

        # If counts are different, definitely affects CSV
        if len(old_event_types) != len(new_event_types):
            return True

        # Compare each event by position (since order matters for editing)
        for old_event, new_event in zip(old_event_types, new_event_types, strict=False):
            if old_event.get("name") != new_event.get("name"):
                return True  # Name changed - affects CSV

        return False

    def _confirm_csv_update(self, actions_text: str = "") -> bool:
        """Ask user to confirm CSV file updates."""
        message = "You have changed event configuration in this project.\n\n"
        if actions_text:
            message += f"The following changes will be applied to events.csv:\n{actions_text}\n\n"
        message += "WARNING: This cannot be undone!\n\nDo you want to update events.csv?"

        reply = QMessageBox.question(
            self,
            "Update Events CSV?",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _get_csv_update_actions(self, _old_config: dict, _new_config: dict) -> str:
        """Generate description of what actions will be taken on CSV files."""
        renames, deleted, added = self._analyze_event_changes()

        actions = []

        # Renames
        for old_name, new_name in renames.items():
            actions.append(f"Rename '{old_name}' → '{new_name}'")

        # Deletions
        for old_name in deleted:
            actions.append(f"Delete '{old_name}'")

        # Additions
        for new_name in added:
            actions.append(f"Add '{new_name}' (empty entries)")

        if actions:
            action_text = "\\n".join(f"• {action}" for action in actions[:10])
            if len(actions) > 10:
                action_text += f"\\n... and {len(actions) - 10} more changes"
            return action_text
        return "No changes detected"

    def _update_existing_csv_files(self, project_path: Path, _old_config: dict, _new_config: dict) -> None:
        """Update all CSV files in project directory with new event names."""
        try:
            # Analyze what operations were performed
            renames, deleted, _added = self._analyze_event_changes()

            # Create name mapping for CSV updates
            name_mapping = {}

            # Add renames to mapping
            name_mapping.update(renames)

            # Mark deleted events for removal
            for deleted_name in deleted:
                name_mapping[deleted_name] = None

            # Find all events.csv files in recording subdirectories
            csv_files = list(project_path.glob("**/events.csv"))

            if not csv_files and not name_mapping:
                return

            updated_files = []
            for csv_file in csv_files:
                if self._update_csv_file(csv_file, name_mapping):  # No need to pass 'added'
                    updated_files.append(csv_file.name)

            # Handle special case: if Accuracy Test was deleted, remove markerInterval.tsv files
            if any("Accuracy Test" in name for name in deleted):
                self._remove_marker_interval_files(project_path)

            if updated_files or any("Accuracy Test" in name for name in deleted):
                QMessageBox.information(self, "Events CSV Updated", "Successfully updated events.csv file.")

        except Exception as e:
            QMessageBox.critical(self, "CSV Update Error", f"Failed to update CSV files:\n{e!s}")

    @staticmethod
    def _update_csv_file(csv_file: Path, name_mapping: dict) -> bool:
        """Update a single CSV file with renames, deletions, and additions."""
        try:
            # Read the CSV file
            with csv_file.open("r", newline="") as infile:
                reader = csv.DictReader(infile)
                rows = list(reader)
                fieldnames = reader.fieldnames

            if not fieldnames:
                return False

            updated = False
            filtered_rows = []

            # Process existing rows: rename/delete
            for row in rows:
                if "event_name" in row and row["event_name"] in name_mapping:
                    new_name = name_mapping[row["event_name"]]
                    if new_name is None:
                        # Delete: skip this row
                        updated = True
                        continue
                    if new_name != row["event_name"]:
                        # Rename: update the name only, preserve all other data
                        row["event_name"] = new_name
                        updated = True

                filtered_rows.append(row)

            # Note: We don't add empty entries for new events - they only exist when actual data is recorded

            # Write back if changes were made
            if updated and fieldnames:
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as temp_file:
                    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(filtered_rows)
                    temp_path = temp_file.name

                # Replace original file
                shutil.move(temp_path, csv_file)
                return True

            return False

        except Exception as e:
            print(f"Error updating {csv_file}: {e}")
            return False

    @staticmethod
    def _remove_marker_interval_files(project_path: Path) -> None:
        """Remove markerInterval.tsv files when Accuracy Test events are deleted."""
        try:
            marker_files = list(project_path.glob("**/markerInterval.tsv"))
            for marker_file in marker_files:
                marker_file.unlink()
        except Exception as e:
            print(f"Error removing marker interval files: {e}")
