"""Metadata input panel."""

from PyQt6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QLineEdit

from ..core.config import ProjectConfig


class MetadataPanel:
    """Metadata input panel component."""

    def __init__(self, parent, config: ProjectConfig):
        self.parent = parent
        self.config = config

    def create_metadata_section(self) -> QGroupBox:
        """Create metadata input section."""
        metadata_group = QGroupBox("Session Metadata")
        metadata_layout = QGridLayout()

        # Participant ID
        metadata_layout.addWidget(QLabel("Participant ID:"), 0, 0)
        self.parent.participant_id_input = QLineEdit()
        self.parent.participant_id_input.textChanged.connect(
            lambda text: self.parent.update_metadata("participant_id", text)
        )
        metadata_layout.addWidget(self.parent.participant_id_input, 0, 1)

        # Condition
        metadata_layout.addWidget(QLabel("Condition:"), 1, 0)
        self.parent.condition_combo = QComboBox()
        self.parent.condition_combo.addItems(self.config.get_conditions())
        self.parent.condition_combo.currentTextChanged.connect(
            lambda text: self.parent.update_metadata("condition", text)
        )
        metadata_layout.addWidget(self.parent.condition_combo, 1, 1)

        # Series Title
        metadata_layout.addWidget(QLabel("Series Title:"), 2, 0)
        self.parent.series_title_input = QLineEdit()
        self.parent.series_title_input.textChanged.connect(
            lambda text: self.parent.update_metadata("series_title", text)
        )
        metadata_layout.addWidget(self.parent.series_title_input, 2, 1)

        metadata_group.setLayout(metadata_layout)
        return metadata_group
