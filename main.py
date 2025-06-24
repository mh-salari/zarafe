"""
Filename:     main.py
Author:       Mohammadhossein Salari, with assistance from Claude 3.7 Sonnet (Anthropic)
Email:        mohammadhossein.salari@gmail.com

Description:  Modified version for muisti branch - Video annotation tool for marking
              approach/viewing events for monitors M1-M4 in eye tracking studies.
              Includes metadata fields and specialized event types.
"""

import sys
import os
import csv
import cv2
import pandas as pd
import platform
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QListWidget,
    QMessageBox,
    QSlider,
    QSplitter,
    QSizePolicy,
    QDialog,
    QLineEdit,
    QComboBox,
    QGridLayout,
    QGroupBox,
)
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QKeyEvent,
    QShortcut,
    QKeySequence,
    QIcon,
    QCursor,
)
from PyQt6.QtCore import Qt, QTimer

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.style as style

import re


class PupilSizePlot(FigureCanvas):
    """Custom matplotlib widget for pupil size visualization"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 2), facecolor='#2b2b2b')
        super().__init__(self.figure)
        self.setParent(parent)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        
        self.pupil_data = None
        self.frame_data = None
        self.total_frames = 0
        
        # Initialize with clean empty state
        self.setup_empty_plot()
    
    def setup_empty_plot(self):
        """Setup a clean empty plot state"""
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        
        # Remove all axes, spines, ticks
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        
        # Set tight layout with no padding
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.draw()
        
    def update_data(self, gaze_data, total_frames):
        """Update pupil size data"""
        self.total_frames = total_frames
        
        if gaze_data is not None and 'pup_diam_r' in gaze_data.columns:
            # Extract frame indices and pupil diameter data
            self.frame_data = gaze_data['frame_idx'].values
            self.pupil_data = gaze_data['pup_diam_r'].values
            
            # Remove NaN values for plotting
            valid_mask = ~np.isnan(self.pupil_data)
            self.frame_data = self.frame_data[valid_mask]
            self.pupil_data = self.pupil_data[valid_mask]
            
            self.plot_data()
        else:
            self.clear_plot()
    
    def plot_data(self):
        """Plot the pupil size data"""
        self.ax.clear()
        
        if self.pupil_data is not None and len(self.pupil_data) > 0:
            # Set dark background
            self.ax.set_facecolor('#2b2b2b')
            
            # Plot pupil size with a nice purple color
            self.ax.plot(self.frame_data, self.pupil_data, color='#8B7AA2', linewidth=1.5, alpha=1.0)
            self.ax.set_xlim(0, self.total_frames)
            
            # Remove all axes, labels and ticks for cleaner look
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            for spine in self.ax.spines.values():
                spine.set_visible(False)
            
            # Add very subtle grid only on y-axis
            self.ax.grid(True, alpha=0.1, color='white', axis='y')
        
        # Remove any padding/margins
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.draw()
    
    def clear_plot(self):
        """Clear the plot and return to clean empty state"""
        self.setup_empty_plot()


# Sort rows by start, handling "N.A." values
def sort_key(row):
    start_value = row[7]  # start_frame column
    if start_value == "N.A.":
        return float("inf")  # Put N.A. values at the end
    try:
        return int(start_value)
    except (ValueError, TypeError):
        return float("inf")  # Treat any non-numeric as N.A.


def apply_dark_theme(app):
    """Apply dark theme based on the current platform"""
    if platform.system() == "Darwin":  # macOS
        app.setProperty("apple_interfaceStyle", "dark")
    elif platform.system() == "Windows":
        os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
        app.setStyle("Fusion")
        app.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMainWindow {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 3px;
                border-radius: 3px;
            }
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                alternate-background-color: #404040;
            }
            QSlider::groove:horizontal {
                background-color: #3c3c3c;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0078d4;
                border: 1px solid #555555;
                width: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 3px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
    else:  # Linux and others
        app.setStyle("Fusion")
        app.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """
        )


def natural_sort_key(s):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", s[0])
    ]


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Zarafe")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        title_label = QLabel("<h2>Video Annotation Tool - Muisti Version</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        desc_text = QLabel(
            "<p>Developed by Mohammadhossein Salari with the assistance of Claude 3.7 Sonnet.</p>"
            "<p>Modified for monitor approach/viewing event annotation.</p>"
            "<p>For more information and source code, please visit:<br>"
            "<a href='https://github.com/mh-salari/zarafe'>https://github.com/mh-salari/zarafe</a></p>"
            "<h3>Acknowledgments</h3>"
            "<p>This project has received funding from the European Union's Horizon "
            "Europe research and innovation funding program under grant "
            "agreement No 101072410, Eyes4ICU project.</p>"
        )
        desc_text.setOpenExternalLinks(True)
        desc_text.setWordWrap(True)
        desc_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_text)

        image_label = QLabel()
        image_path = os.path.join(
            os.path.dirname(__file__), "resources", "Funded_by_EU_Eyes4ICU.png"
        )

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(
                pixmap.scaled(
                    400,
                    100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            image_label.setText("Image not found: " + image_path)

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        self.setLayout(layout)


class VideoAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()

        # Video state variables
        self.video_paths = []
        self.current_video_index = -1
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.playing = False
        self.fps = 30
        self.last_frame_read = -1  # Track last frame read for sequential optimization

        # Gaze data
        self.gaze_data = None
        self.frame_to_gaze = {}

        # Timer for playback
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

        # Annotation storage
        self.events = []
        self.selected_event = None
        self.event_history = []  # For undo functionality
        self.has_unsaved_changes = False  # Track unsaved changes

        # Metadata fields
        self.metadata = {
            "participant_id": "",
            "condition": "",
            "series_title": "",
            "file_name": "",
        }

        # Predefined event types
        self.event_types = [
            "Approach M1",
            "View M1",
            "Approach M2",
            "View M2",
            "Approach M3",
            "View M3",
            "Approach M4",
            "View M4",
        ]

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.showMaximized()

    def setup_ui(self):
        self.setWindowTitle("Zarafe - Muisti Version")

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.open_dir_btn = QPushButton("Open Directory")
        self.open_dir_btn.clicked.connect(self.open_directory)
        left_layout.addWidget(self.open_dir_btn)

        nav_layout = QHBoxLayout()
        self.prev_video_btn = QPushButton("Previous Video")
        self.prev_video_btn.clicked.connect(self.prev_video)
        self.next_video_btn = QPushButton("Next Video")
        self.next_video_btn.clicked.connect(self.next_video)
        nav_layout.addWidget(self.prev_video_btn)
        nav_layout.addWidget(self.next_video_btn)
        left_layout.addLayout(nav_layout)

        left_layout.addWidget(QLabel("Videos:"))
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.select_video)
        left_layout.addWidget(self.video_list)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        self.video_label = QLabel("No video selected")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        center_layout.addWidget(self.video_label, 1)
        
        self.annotation_info_label = QLabel("")
        self.annotation_info_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.annotation_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.annotation_info_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.annotation_info_label.setParent(self.video_label)
        self.annotation_info_label.hide()

        control_layout = QVBoxLayout()

        pupil_label = QLabel("Pupil Diameter (mm)")
        pupil_label.setStyleSheet("color: white; font-size: 12px; margin-bottom: 2px;")
        pupil_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        control_layout.addWidget(pupil_label)
        
        self.pupil_plot = PupilSizePlot()
        self.pupil_plot.setMaximumHeight(120)
        control_layout.addWidget(self.pupil_plot)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.valueChanged.connect(self.slider_moved)
        control_layout.addWidget(self.timeline_slider)

        playback_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_play)
        self.prev_frame_btn = QPushButton("← Previous Frame")
        self.prev_frame_btn.clicked.connect(self.prev_frame)
        self.next_frame_btn = QPushButton("Next Frame →")
        self.next_frame_btn.clicked.connect(self.next_frame)
        self.frame_info = QLabel("Frame: 0 / 0")

        playback_layout.addWidget(self.play_btn)
        playback_layout.addWidget(self.prev_frame_btn)
        playback_layout.addWidget(self.next_frame_btn)
        playback_layout.addStretch()
        playback_layout.addWidget(self.frame_info)
        control_layout.addLayout(playback_layout)

        center_layout.addLayout(control_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        metadata_group = QGroupBox("Session Metadata")
        metadata_layout = QGridLayout()

        metadata_layout.addWidget(QLabel("Participant ID:"), 0, 0)
        self.participant_id_input = QLineEdit()
        self.participant_id_input.textChanged.connect(
            lambda text: self.update_metadata("participant_id", text)
        )
        metadata_layout.addWidget(self.participant_id_input, 0, 1)

        metadata_layout.addWidget(QLabel("Condition:"), 1, 0)
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["", "Dark", "Timed Dark", "Normal"])
        self.condition_combo.currentTextChanged.connect(
            lambda text: self.update_metadata("condition", text)
        )
        metadata_layout.addWidget(self.condition_combo, 1, 1)

        metadata_layout.addWidget(QLabel("Series Title:"), 2, 0)
        self.series_title_input = QLineEdit()
        self.series_title_input.textChanged.connect(
            lambda text: self.update_metadata("series_title", text)
        )
        metadata_layout.addWidget(self.series_title_input, 2, 1)

        metadata_group.setLayout(metadata_layout)
        right_layout.addWidget(metadata_group)

        event_creation_layout = QVBoxLayout()
        event_creation_layout.addWidget(QLabel("Create Event:"))

        self.event_type_combo = QComboBox()
        self.event_type_combo.addItem("Select event type...")
        self.event_type_combo.addItems(self.event_types)
        event_creation_layout.addWidget(self.event_type_combo)

        self.create_event_btn = QPushButton("Create Selected Event")
        self.create_event_btn.clicked.connect(self.create_event)
        event_creation_layout.addWidget(self.create_event_btn)

        right_layout.addLayout(event_creation_layout)

        right_layout.addWidget(QLabel("Events:"))
        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(200)  # Limit height for 5-6 items
        self.events_list.itemClicked.connect(self.select_event)
        self.events_list.itemDoubleClicked.connect(self.jump_to_event)
        right_layout.addWidget(self.events_list)

        event_controls = QVBoxLayout()

        button_row1 = QHBoxLayout()
        self.mark_start_btn = QPushButton("Mark Start")
        self.mark_start_btn.clicked.connect(self.mark_start)
        self.mark_end_btn = QPushButton("Mark End")
        self.mark_end_btn.clicked.connect(self.mark_end)
        button_row1.addWidget(self.mark_start_btn)
        button_row1.addWidget(self.mark_end_btn)

        button_row2 = QHBoxLayout()
        self.delete_event_btn = QPushButton("Delete Event")
        self.delete_event_btn.clicked.connect(self.delete_event)
        self.save_events_btn = QPushButton("Save Events")
        self.save_events_btn.clicked.connect(self.save_events)
        button_row2.addWidget(self.delete_event_btn)
        button_row2.addWidget(self.save_events_btn)

        event_controls.addLayout(button_row1)
        event_controls.addLayout(button_row2)

        right_layout.addLayout(event_controls)
        right_layout.addStretch(1)  # Add stretch to keep controls at top

        # Add keyboard shortcuts above the About link
        shortcuts_label = QLabel("<h4>Keyboard Shortcuts</h4>")
        shortcuts_label.setStyleSheet("color: white")
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(shortcuts_label)

        # Keyboard shortcuts list
        shortcuts_text = QLabel(
            "Space: Play/Pause\n"
            "Left Arrow: Previous Frame\n"
            "Right Arrow: Next Frame\n"
            "Shift+Left Arrow: Jump 10 Frames Back\n"
            "Shift+Right Arrow: Jump 10 Frames Forward\n"
            "Ctrl+Z: Undo Action\n"
            "Ctrl+S: Save Events\n"
        )
        shortcuts_text.setStyleSheet("color: white")
        shortcuts_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(shortcuts_text)

        # Add "About" text link at the bottom
        about_label = QLabel("About")
        about_label.setStyleSheet("color: white; text-decoration: underline;")
        about_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        about_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Use a lambda for the click event
        about_label.mousePressEvent = lambda event: (
            self.show_about_dialog()
            if event.button() == Qt.MouseButton.LeftButton
            else None
        )

        right_layout.addWidget(about_label)

        # Add all panels to the main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)

        # Set proportional sizes (narrow sides, big center)
        main_splitter.setSizes([100, 900, 100])

        self.setCentralWidget(main_splitter)

        # Set up keyboard shortcuts
        self.setup_shortcuts()

        # Enable keyboard focus for arrow key navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def update_metadata(self, field, value):
        """Update metadata field and mark as having unsaved changes"""
        self.metadata[field] = value
        if self.cap is not None:  # Only mark as unsaved if a video is loaded
            self.has_unsaved_changes = True

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def setup_shortcuts(self):
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_action)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_events)
        
        self.play_pause_shortcut = QShortcut(QKeySequence("Space"), self)
        self.play_pause_shortcut.activated.connect(self.toggle_play)
        
        self.next_frame_shortcut = QShortcut(QKeySequence("Right"), self)
        self.next_frame_shortcut.activated.connect(self.next_frame)
        
        self.prev_frame_shortcut = QShortcut(QKeySequence("Left"), self)
        self.prev_frame_shortcut.activated.connect(self.prev_frame)
        
        self.jump_forward_shortcut = QShortcut(QKeySequence("Shift+Right"), self)
        self.jump_forward_shortcut.activated.connect(self.jump_forward_10)
        
        self.jump_backward_shortcut = QShortcut(QKeySequence("Shift+Left"), self)
        self.jump_backward_shortcut.activated.connect(self.jump_backward_10)

    def open_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not dir_path:
            return

        self.video_paths.clear()
        self.video_list.clear()

        video_entries = []

        for entry in os.scandir(dir_path):
            if entry.is_dir():
                video_path = os.path.join(entry.path, "worldCamera.mp4")
                if os.path.exists(video_path):
                    display_name = f"{os.path.basename(entry.path)}"
                    video_entries.append((video_path, display_name))

        video_entries.sort(key=natural_sort_key)

        for video_path, display_name in video_entries:
            self.video_paths.append(video_path)
            self.video_list.addItem(display_name)

    def select_video(self, item):
        index = self.video_list.row(item)
        if 0 <= index < len(self.video_paths):
            self.load_video(index)

    def next_video(self):
        if not self.video_paths:
            return

        if self.current_video_index < len(self.video_paths) - 1:
            self.load_video(self.current_video_index + 1)
            self.video_list.setCurrentRow(self.current_video_index)

    def prev_video(self):
        if not self.video_paths:
            return

        if self.current_video_index > 0:
            self.load_video(self.current_video_index - 1)
            self.video_list.setCurrentRow(self.current_video_index)

    def check_unsaved_changes(self):
        """Check if there are unsaved changes and prompt user to save"""
        if not self.has_unsaved_changes:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Would you like to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            # Save changes
            self.save_events()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            # Proceed without saving
            return True
        else:
            # Cancel the operation
            return False

    def load_video(self, index):
        if self.cap is not None and not self.check_unsaved_changes():
            return

        if self.cap is not None:
            self.cap.release()
            self.timer.stop()

        self.current_video_index = index
        self.events.clear()
        self.events_list.clear()
        self.selected_event = None
        self.event_history.clear()
        self.frame_to_gaze = {}
        self.has_unsaved_changes = False

        # Open the new video
        video_path = self.video_paths[index]
        video_dir = os.path.dirname(video_path)
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            self.video_label.setText(f"Error opening video: {video_path}")
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.last_frame_read = -1
        self.playing = False
        self.play_btn.setText("Play")

        self.timeline_slider.setMaximum(self.total_frames - 1)
        self.timeline_slider.setValue(0)

        self.metadata["file_name"] = os.path.basename(video_dir)

        gaze_path = os.path.join(video_dir, "gazeData.tsv")
        if os.path.exists(gaze_path):
            try:
                self.load_gaze_data(gaze_path)
            except Exception as e:
                print(f"Error loading gaze data: {e}")

        self.pupil_plot.update_data(self.gaze_data, self.total_frames)

        self.display_frame()

        metadata_path = os.path.join(video_dir, "metadata.csv")
        if os.path.exists(metadata_path):
            self.load_metadata_csv(metadata_path)

        csv_path = os.path.join(video_dir, "events.csv")
        if os.path.exists(csv_path):
            self.load_events(csv_path)
            self.save_event_state()

    def load_gaze_data(self, gaze_path):
        """Load gaze data from TSV file and organize by frame index"""
        self.gaze_data = pd.read_csv(gaze_path, sep="\t")

        self.frame_to_gaze = {}

        for _, row in self.gaze_data.iterrows():
            frame_idx = int(row["frame_idx"])

            if pd.isna(row["gaze_pos_vid_x"]) or pd.isna(row["gaze_pos_vid_y"]):
                continue
            x = float(row["gaze_pos_vid_x"])
            y = float(row["gaze_pos_vid_y"])

            if frame_idx not in self.frame_to_gaze:
                self.frame_to_gaze[frame_idx] = []

            self.frame_to_gaze[frame_idx].append((x, y))

    def jump_to_event(self, item):
        """Jump to the start or end of the selected event when double-clicked"""
        index = self.events_list.row(item)
        if 0 <= index < len(self.events):
            event = self.events[index]

            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                if event["end"] != -1:
                    self.current_frame = event["end"]
                    self.last_frame_read = -1
                    self.display_frame()
            else:
                if event["start"] != -1:
                    self.current_frame = event["start"]
                    self.last_frame_read = -1
                    self.display_frame()
                elif event["end"] != -1:
                    self.current_frame = event["end"]
                    self.last_frame_read = -1
                    self.display_frame()

    def display_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        if self.current_frame != self.last_frame_read + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # Update last frame read
        self.last_frame_read = self.current_frame

        if self.current_frame in self.frame_to_gaze:
            for x, y in self.frame_to_gaze[self.current_frame]:
                h, w = frame.shape[:2]
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(
                        frame, (int(x), int(y)), 5, (0, 255, 0), -1
                    )

        # Check if current frame is within any event, and add border if it is
        frame_in_event = False
        event_color = None
        current_event = None
        for event in self.events:
            if (
                event["start"] != -1
                and event["end"] != -1
                and event["start"] <= self.current_frame + 1 <= event["end"]
            ):
                frame_in_event = True
                current_event = event
                event_color = (
                    (123, 100, 25) if "View" in event["name"] else (123, 171, 61)
                )
                break

        if frame_in_event:
            h, w = frame.shape[:2]
            border_thickness = 1
            frame = cv2.copyMakeBorder(
                frame,
                border_thickness,
                border_thickness,
                border_thickness,
                border_thickness,
                cv2.BORDER_CONSTANT,
                value=event_color,
            )
            
            if current_event:
                duration = self.calculate_duration(current_event["start"], current_event["end"])
                duration_str = f"{duration}s" if duration is not None else "N/A"
                
                event_type = "Approach" if "Approach" in current_event["name"] else "View"
                monitor = current_event["name"].split()[-1]
                annotation_text = f"{event_type} {monitor} ({duration_str})"
                
                color_hex = f"#{event_color[2]:02x}{event_color[1]:02x}{event_color[0]:02x}"
                
                self.annotation_info_label.setText(annotation_text)
                self.annotation_info_label.setStyleSheet(f"color: {color_hex}; font-size: 14px; font-weight: bold;")
                self.annotation_info_label.adjustSize()  # Resize to fit content
                
                # Position the label at top-left of the actual video image
                self.position_annotation_overlay()
                self.annotation_info_label.show()
        else:
            self.annotation_info_label.hide()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, w * ch, QImage.Format.Format_RGB888)

        self.video_label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        )

        self.frame_info.setText(
            f"Frame: {self.current_frame + 1} / {self.total_frames}"
        )

        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(self.current_frame)
        self.timeline_slider.blockSignals(False)


    def position_annotation_overlay(self):
        """Position the annotation overlay at the top-left of the actual video image"""
        if not self.video_label.pixmap():
            return
            
        # Get the video label size and the pixmap size
        label_size = self.video_label.size()
        pixmap_size = self.video_label.pixmap().size()
        
        # Calculate the actual position of the video image within the label
        # (accounting for aspect ratio scaling and centering)
        label_width = label_size.width()
        label_height = label_size.height()
        pixmap_width = pixmap_size.width()
        pixmap_height = pixmap_size.height()
        
        # Calculate scaling factor (keeping aspect ratio)
        scale_x = label_width / pixmap_width
        scale_y = label_height / pixmap_height
        scale = min(scale_x, scale_y)
        
        # Calculate actual displayed image size
        display_width = int(pixmap_width * scale)
        display_height = int(pixmap_height * scale)
        
        # Calculate offset to center the image in the label
        offset_x = (label_width - display_width) // 2
        offset_y = (label_height - display_height) // 2
        
        # Position the annotation at top-left of the actual video image with small margin
        self.annotation_info_label.move(offset_x + 10, offset_y + 10)

    def slider_moved(self):
        if self.cap is None or not self.cap.isOpened():
            return

        self.current_frame = self.timeline_slider.value()
        self.last_frame_read = -1
        self.display_frame()

    def next_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.display_frame()
        else:
            if self.playing:
                self.toggle_play()

    def prev_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        if self.current_frame > 0:
            self.current_frame -= 1
            self.display_frame()

    def toggle_play(self):
        if self.cap is None or not self.cap.isOpened():
            return

        self.playing = not self.playing

        if self.playing:
            self.play_btn.setText("Pause")
            interval = int(1000 / self.fps) if self.fps > 0 else 33
            self.timer.start(interval)
        else:
            self.play_btn.setText("Play")
            self.timer.stop()

    def save_event_state(self):
        """Save current state of events for undo functionality"""
        state_copy = []
        for event in self.events:
            state_copy.append(event.copy())
        self.event_history.append(state_copy)

        if len(self.event_history) > 20:
            self.event_history.pop(0)

    def undo_action(self):
        """Undo the last event-related action"""
        if not self.event_history:
            return

        prev_selected = self.selected_event

        self.events = self.event_history.pop()

        if self.events:
            self.has_unsaved_changes = True

        self.update_event_list()

        if prev_selected is not None and prev_selected < len(self.events):
            self.selected_event = prev_selected
            self.events_list.setCurrentRow(prev_selected)
        else:
            self.selected_event = None

    def create_event(self):
        """Create a new event of the selected type"""
        if self.cap is None:
            QMessageBox.warning(self, "Warning", "Please load a video first.")
            return

        selected_type = self.event_type_combo.currentText()
        if selected_type == "Select event type...":
            QMessageBox.warning(self, "Warning", "Please select an event type.")
            return

        for event in self.events:
            if event["name"] == selected_type:
                QMessageBox.warning(
                    self,
                    "Event Exists",
                    f"{selected_type} already exists. Please complete or delete it first.",
                )
                for i, e in enumerate(self.events):
                    if e["name"] == selected_type:
                        self.selected_event = i
                        self.events_list.setCurrentRow(i)
                return

        self.save_event_state()

        event = {"name": selected_type, "start": -1, "end": -1}
        self.events.append(event)
        self.selected_event = len(self.events) - 1
        self.has_unsaved_changes = True

        self.event_type_combo.setCurrentIndex(0)

        self.update_event_list()

    def select_event(self, item):
        index = self.events_list.row(item)
        if 0 <= index < len(self.events):
            self.selected_event = index

    def mark_start(self):
        if self.cap is None:
            return

        if self.selected_event is None:
            QMessageBox.warning(
                self, "Warning", "Please create or select an event first."
            )
            return

        self.save_event_state()

        if (
            self.events[self.selected_event]["end"] != -1
            and self.current_frame > self.events[self.selected_event]["end"]
        ):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Start frame cannot be after end frame. Please mark start before end.",
            )
            return

        self.events[self.selected_event]["start"] = self.current_frame
        self.has_unsaved_changes = True
        self.update_event_list()

    def mark_end(self):
        if self.cap is None:
            return

        if self.selected_event is None:
            QMessageBox.warning(
                self, "Warning", "Please create or select an event first."
            )
            return

        self.save_event_state()

        if (
            self.events[self.selected_event]["start"] != -1
            and self.current_frame < self.events[self.selected_event]["start"]
        ):
            QMessageBox.warning(
                self,
                "Invalid Input",
                "End frame cannot be before start frame. Please mark end after start.",
            )
            return

        self.events[self.selected_event]["end"] = self.current_frame
        self.has_unsaved_changes = True
        self.update_event_list()

    def delete_event(self):
        if self.selected_event is None:
            QMessageBox.warning(self, "Warning", "Please select an event to delete.")
            return

        if 0 <= self.selected_event < len(self.events):
            self.save_event_state()

            self.events.pop(self.selected_event)

            if not self.events:
                self.selected_event = None
            elif self.selected_event >= len(self.events):
                self.selected_event = len(self.events) - 1

            self.has_unsaved_changes = True
            self.update_event_list()

    def update_event_list(self):
        self.events_list.clear()

        for event in self.events:
            start_str = str(event["start"]) if event["start"] != -1 else "N/A"
            end_str = str(event["end"]) if event["end"] != -1 else "N/A"
            self.events_list.addItem(
                f"{event['name']}: Start={start_str}, End={end_str}"
            )

        if self.selected_event is not None:
            self.events_list.setCurrentRow(self.selected_event)

    def calculate_duration(self, start_frame, end_frame):
        """Calculate duration in seconds from frame numbers"""
        if start_frame == -1 or end_frame == -1 or self.fps == 0:
            return None
        return round((end_frame - start_frame + 1) / self.fps, 1)

    def save_events(self):
        if self.cap is None or self.current_video_index < 0:
            return

        # Check metadata completeness
        if not all(
            [
                self.metadata["participant_id"],
                self.metadata["condition"],
                self.metadata["series_title"],
            ]
        ):
            QMessageBox.warning(
                self,
                "Incomplete Metadata",
                "Please fill in all metadata fields (Participant ID, Condition, Series Title) before saving.",
            )
            return

        video_dir = os.path.dirname(self.video_paths[self.current_video_index])
        csv_path = os.path.join(video_dir, "events.csv")

        try:
            annotated_monitors = set()
            rows_to_write = []

            for event in self.events:
                parts = event["name"].split()
                if len(parts) >= 2:
                    monitor_id = parts[-1]
                    event_type = "approach" if "Approach" in event["name"] else "view"
                    annotated_monitors.add(monitor_id)

                    if event["start"] == -1 or event["end"] == -1:
                        QMessageBox.warning(
                            self,
                            "Incomplete Event",
                            f"Event '{event['name']}' is missing start or end time. Please complete the annotation before saving.",
                        )
                        return

                    duration = self.calculate_duration(event["start"], event["end"])
                    duration_str = str(duration) if duration is not None else "N.A."

                    image_name = self.metadata.get(monitor_id, "")

                    row = [
                        self.metadata["participant_id"],
                        self.metadata["file_name"],
                        self.metadata["condition"],
                        self.metadata["series_title"],
                        image_name,
                        monitor_id,
                        event_type,
                        event["start"] if event["start"] != -1 else "N.A.",
                        event["end"] if event["end"] != -1 else "N.A.",
                        duration_str,
                    ]
                    rows_to_write.append(row)

            all_monitors = {"M1", "M2", "M3", "M4"}
            missing_monitors = all_monitors - annotated_monitors

            for monitor_id in missing_monitors:
                image_name = self.metadata.get(monitor_id, "")

                na_row = [
                    self.metadata["participant_id"],
                    self.metadata["file_name"],
                    self.metadata["condition"],
                    self.metadata["series_title"],
                    image_name,
                    monitor_id,
                    "N.A.",
                    "N.A.",
                    "N.A.",
                    "N.A.",
                ]
                rows_to_write.append(na_row)

            rows_to_write.sort(key=sort_key)

            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "participant_id",
                        "file_name",
                        "condition",
                        "series_title",
                        "image_name",
                        "monitor_id",
                        "event_type",
                        "start_frame",
                        "end_frame",
                        "duration",
                    ]
                )
                writer.writerows(rows_to_write)

            self.has_unsaved_changes = False
            QMessageBox.information(self, "Success", f"Events saved to {csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save events: {str(e)}")

    def load_events(self, csv_path):
        self.events.clear()

        try:
            with open(csv_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:

                    if row.get("event_type", "") == "N.A.":
                        continue

                    monitor_id = row.get("monitor_id", "")
                    event_type = row.get("event_type", "")

                    if event_type == "approach":
                        event_name = f"Approach {monitor_id}"
                    elif event_type == "view":
                        event_name = f"View {monitor_id}"
                    else:
                        continue

                    start_frame = row.get("start_frame", "N.A.")
                    end_frame = row.get("end_frame", "N.A.")

                    event = {
                        "name": event_name,
                        "start": (
                            int(start_frame)
                            if start_frame not in ["-1", "N.A."]
                            else -1
                        ),
                        "end": (
                            int(end_frame) if end_frame not in ["-1", "N.A."] else -1
                        ),
                    }
                    self.events.append(event)

            self.has_unsaved_changes = False

            self.update_event_list()

            if self.events:
                self.selected_event = 0
                self.events_list.setCurrentRow(0)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading events: {e}")

    def update_metadata_ui(self):
        """Update metadata UI fields with current metadata values"""

        self.participant_id_input.setText(self.metadata["participant_id"])
        self.condition_combo.setCurrentText(self.metadata["condition"])
        self.series_title_input.setText(self.metadata["series_title"])

    def load_metadata_csv(self, metadata_path):
        """Load metadata from CSV file and prefill UI fields"""
        try:
            with open(metadata_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    self.metadata["participant_id"] = row.get("participant_id", "")
                    self.metadata["condition"] = row.get("condition", "")
                    self.metadata["series_title"] = row.get("series_title", "")

                    self.metadata["M1"] = row.get("monitor_1_image", "")
                    self.metadata["M2"] = row.get("monitor_2_image", "")
                    self.metadata["M3"] = row.get("monitor_3_image", "")
                    self.metadata["M4"] = row.get("monitor_4_image", "")

                    break

            self.update_metadata_ui()

        except Exception as e:
            print(f"Error loading metadata CSV: {e}")

    def jump_forward_10(self):
        """Jump 10 frames forward"""
        if self.cap is None or not self.cap.isOpened():
            return
        
        target_frame = min(self.current_frame + 10, self.total_frames - 1)
        if target_frame != self.current_frame:
            self.current_frame = target_frame
            self.last_frame_read = -1
            self.display_frame()

    def jump_backward_10(self):
        """Jump 10 frames backward"""
        if self.cap is None or not self.cap.isOpened():
            return
        
        target_frame = max(self.current_frame - 10, 0)
        if target_frame != self.current_frame:
            self.current_frame = target_frame
            self.last_frame_read = -1
            self.display_frame()

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save them before exiting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_events()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        if self.cap is not None:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    apply_dark_theme(app)

    player = VideoAnnotator()
    player.show()
    sys.exit(app.exec())
