"""New project creation dialog."""

import json
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QFormLayout,
    QGroupBox, QSpinBox, QColorDialog, QMessageBox, QCheckBox,
    QFileDialog, QTextEdit, QScrollArea, QWidget
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
        self.setModal(True)
        
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
        
        # Pre-defined event templates
        template_layout = QHBoxLayout()
        accuracy_test_btn = QPushButton("Add Accuracy Test (glassesValidator)")
        accuracy_test_btn.clicked.connect(self.add_accuracy_test_event)
        custom_event_btn = QPushButton("Add Custom Event")
        custom_event_btn.clicked.connect(self.add_custom_event)
        template_layout.addWidget(accuracy_test_btn)
        template_layout.addWidget(custom_event_btn)
        events_layout.addLayout(template_layout)
        
        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(100)
        events_layout.addWidget(self.events_list)
        
        scroll_layout.addWidget(events_group)
        
        
        # Metadata Fields
        metadata_group = QGroupBox("Metadata Fields")
        metadata_layout = QVBoxLayout(metadata_group)
        
        metadata_desc = QLabel("Additional data fields to collect (participant info, session details)")
        metadata_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        metadata_layout.addWidget(metadata_desc)
        
        # Standard fields (always included)
        self.participant_id_cb = QCheckBox("Participant ID")
        self.participant_id_cb.setChecked(True)
        self.participant_id_cb.setEnabled(False)  # Always required
        
        self.file_name_cb = QCheckBox("File Name")  
        self.file_name_cb.setChecked(True)
        self.file_name_cb.setEnabled(False)  # Always required
        
        metadata_layout.addWidget(self.participant_id_cb)
        metadata_layout.addWidget(self.file_name_cb)
        
        scroll_layout.addWidget(metadata_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("Create Project Configuration")
        self.create_btn.setObjectName("createBtn")
        self.create_btn.clicked.connect(self.create_project)
        self.create_btn.setMinimumHeight(40)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(40)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
            
    def add_accuracy_test_event(self) -> None:
        """Add accuracy test event for glassesValidator."""
        accuracy_item = QListWidgetItem("Accuracy Test - glassesValidator format")
        accuracy_item.setData(Qt.ItemDataRole.UserRole, {"name": "Accuracy Test", "applies_to": "glassesValidator"})
        self.events_list.addItem(accuracy_item)
        
    def add_custom_event(self) -> None:
        """Add a custom single event."""
        from PyQt6.QtWidgets import QInputDialog
        event_name, ok = QInputDialog.getText(self, "Custom Event", "Enter event name:")
        if ok and event_name.strip():
            item = QListWidgetItem(f"{event_name.strip()} - single event")
            item.setData(Qt.ItemDataRole.UserRole, {"name": event_name.strip(), "applies_to": "global"})
            self.events_list.addItem(item)
            
            
    def create_project(self) -> None:
        """Create the project configuration."""
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter a project name.")
            return
            
        if self.events_list.count() == 0:
            QMessageBox.warning(self, "Missing Information", "Please add at least one event type.")
            return
            
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
            "project": {
                "name": self.project_name_input.text().strip()
            },
            "targets": [],  # Empty for time-based annotations
            "event_types": [],
            "conditions": [""],  # Always include empty option
            "color_rules": [
                {"pattern": "Accuracy", "color": [123, 100, 25]}
            ],
            "default_color": [123, 171, 61],
            "metadata_schema": {
                "participant_id": {"type": "text", "required": True},
                "file_name": {"type": "text", "required": True}
            }
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
                "You can now add video files to this directory and open the project in Zarafe."
            )
            
            self.project_path = project_path
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save project configuration:\n{str(e)}"
            )
            
    def get_project_path(self) -> Path | None:
        """Get the created project path."""
        return getattr(self, 'project_path', None)