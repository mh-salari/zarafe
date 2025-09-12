"""Video playback controls widget."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

from ..core.config import ProjectConfig
from .pupil_plot import PupilSizePlot


class VideoControls:
    """Video playback controls component."""

    def __init__(self, parent, config: ProjectConfig = None):
        self.parent = parent
        self.config = config

    def setup_controls(self) -> QVBoxLayout:
        """Create video controls layout."""
        control_layout = QVBoxLayout()

        # Pupil size plot
        pupil_label = QLabel("Pupil Diameter (mm)")
        pupil_label.setStyleSheet("color: white; font-size: 12px; margin-bottom: 2px;")
        pupil_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        control_layout.addWidget(pupil_label)

        if self.config:
            self.parent.pupil_plot = PupilSizePlot(self.config)
        else:
            # Fallback for when config is not available yet
            self.parent.pupil_plot = None
        
        if self.parent.pupil_plot:
            self.parent.pupil_plot.setMaximumHeight(120)
            control_layout.addWidget(self.parent.pupil_plot)

        # Timeline slider
        self.parent.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.timeline_slider.setMinimum(0)
        self.parent.timeline_slider.setMaximum(100)
        self.parent.timeline_slider.valueChanged.connect(self.parent.slider_moved)
        control_layout.addWidget(self.parent.timeline_slider)

        # Playback buttons
        playback_layout = self.create_playback_buttons()
        control_layout.addLayout(playback_layout)

        return control_layout

    def create_playback_buttons(self) -> QHBoxLayout:
        """Create playback button layout."""
        playback_layout = QHBoxLayout()

        self.parent.play_btn = QPushButton("Play")
        self.parent.play_btn.clicked.connect(self.parent.toggle_play)
        self.parent.prev_frame_btn = QPushButton("← Previous Frame")
        self.parent.prev_frame_btn.clicked.connect(self.parent.prev_frame)
        self.parent.next_frame_btn = QPushButton("Next Frame →")
        self.parent.next_frame_btn.clicked.connect(self.parent.next_frame)
        self.parent.frame_info = QLabel("Frame: 0 / 0")

        playback_layout.addWidget(self.parent.play_btn)
        playback_layout.addWidget(self.parent.prev_frame_btn)
        playback_layout.addWidget(self.parent.next_frame_btn)
        playback_layout.addStretch()
        playback_layout.addWidget(self.parent.frame_info)

        return playback_layout
