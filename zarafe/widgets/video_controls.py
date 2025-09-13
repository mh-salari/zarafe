"""Video playback controls widget."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

from .pupil_plot import PupilSizePlot

# Control constants
PUPIL_LABEL_FONT_SIZE = 12
PUPIL_PLOT_MAX_HEIGHT = 120
SLIDER_MAX_VALUE = 100
MUTE_BUTTON_WIDTH = 40


class VideoControls:
    """Video playback controls component."""

    def __init__(self, parent: object) -> None:
        """Initialize the video controls component."""
        self.parent = parent

    def setup_controls(self) -> QVBoxLayout:
        """Setup video control layout."""
        control_layout = QVBoxLayout()

        # Pupil size plot
        pupil_label = QLabel("Pupil Diameter (mm)")
        pupil_label.setStyleSheet(f"color: white; font-size: {PUPIL_LABEL_FONT_SIZE}px; margin-bottom: 2px;")
        pupil_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        control_layout.addWidget(pupil_label)

        self.parent.pupil_plot = PupilSizePlot()
        if self.parent.pupil_plot:
            self.parent.pupil_plot.setMaximumHeight(PUPIL_PLOT_MAX_HEIGHT)
            control_layout.addWidget(self.parent.pupil_plot)

        # Timeline slider
        self.parent.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.timeline_slider.setMinimum(0)
        self.parent.timeline_slider.setMaximum(SLIDER_MAX_VALUE)
        self.parent.timeline_slider.valueChanged.connect(self.parent.slider_moved)
        control_layout.addWidget(self.parent.timeline_slider)

        # Playback buttons
        playback_layout = self.create_playback_buttons()
        control_layout.addLayout(playback_layout)

        return control_layout

    def create_playback_buttons(self) -> QHBoxLayout:
        """Create playback control buttons."""
        playback_layout = QHBoxLayout()

        self.parent.play_btn = QPushButton("Play")
        self.parent.play_btn.clicked.connect(self.parent.toggle_play)
        self.parent.prev_frame_btn = QPushButton("← Previous Frame")
        self.parent.prev_frame_btn.clicked.connect(self.parent.prev_frame)
        self.parent.next_frame_btn = QPushButton("Next Frame →")
        self.parent.next_frame_btn.clicked.connect(self.parent.next_frame)

        # Mute button
        self.parent.mute_btn = QPushButton("🔊")
        self.parent.mute_btn.clicked.connect(self.parent.toggle_mute)
        self.parent.mute_btn.setMaximumWidth(MUTE_BUTTON_WIDTH)

        self.parent.frame_info = QLabel("Frame: 0 / 0")

        playback_layout.addWidget(self.parent.play_btn)
        playback_layout.addWidget(self.parent.prev_frame_btn)
        playback_layout.addWidget(self.parent.next_frame_btn)
        playback_layout.addWidget(self.parent.mute_btn)
        playback_layout.addStretch()
        playback_layout.addWidget(self.parent.frame_info)

        return playback_layout
