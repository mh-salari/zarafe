"""Metadata input panel."""

from PyQt6.QtWidgets import QLabel


from ..core.config import ProjectConfig


class MetadataPanel:
    """Metadata input panel component."""

    def __init__(self, parent, config: ProjectConfig):
        self.parent = parent
        self.config = config

    def create_metadata_section(self) -> QLabel:
        """Create simple file name display."""
        self.parent.file_info_label = QLabel("No file loaded")
        self.parent.file_info_label.setStyleSheet("color: #cccccc; font-style: italic; padding: 5px;")
        return self.parent.file_info_label
