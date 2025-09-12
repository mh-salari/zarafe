"""Metadata input panel."""

from PyQt6.QtWidgets import QLabel

from ..core.config import ProjectConfig


# UI Constants
DEFAULT_FILE_COLOR = "#cccccc"
PANEL_PADDING = "5px"


class MetadataPanel:
    """Metadata input panel component."""

    def __init__(self, parent, config: ProjectConfig):
        self.parent = parent
        self.config = config

    def create_metadata_section(self) -> QLabel:
        """Create simple file name display."""
        file_info_label = QLabel("No file loaded")
        file_info_label.setStyleSheet(f"color: {DEFAULT_FILE_COLOR}; font-style: italic; padding: {PANEL_PADDING};")
        self.parent.file_info_label = file_info_label
        return file_info_label
