"""
Filename:     main.py
Author:       Mohammadhossein Salari, with assistance from Claude 3.7 Sonnet (Anthropic)
Email:        mohammadhossein.salari@gmail.com

Description:  Single-file implementation of Zarafe, a video annotation tool designed for marking
              time events in eye tracking videos with gaze data visualization. This standalone
              script handles all functionality including video loading, gaze data overlay,
              event annotation creation/management, and export functionality.
"""

import sys
import os
import csv
import cv2
import pandas as pd
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


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Zarafe")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("<h2>Video Annotation Tool</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description text
        desc_text = QLabel(
            "<p>Developed by Mohammadhossein Salari with the assistance of Claude 3.7 Sonnet.</p>"
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

        # Add image
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

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.showMaximized()

    def setup_ui(self):
        self.setWindowTitle("Zarafe")

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ===== LEFT PANEL =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Open directory button
        self.open_dir_btn = QPushButton("Open Directory")
        self.open_dir_btn.clicked.connect(self.open_directory)
        left_layout.addWidget(self.open_dir_btn)

        # Video navigation buttons 
        nav_layout = QHBoxLayout()
        self.prev_video_btn = QPushButton("Previous Video")
        self.prev_video_btn.clicked.connect(self.prev_video)
        self.next_video_btn = QPushButton("Next Video")
        self.next_video_btn.clicked.connect(self.next_video)
        nav_layout.addWidget(self.prev_video_btn)
        nav_layout.addWidget(self.next_video_btn)
        left_layout.addLayout(nav_layout)

        # Video list
        left_layout.addWidget(QLabel("Videos:"))
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.select_video)
        left_layout.addWidget(self.video_list)

        # ===== CENTER PANEL =====
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # Video display
        self.video_label = QLabel("No video selected")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        center_layout.addWidget(self.video_label, 1)

        # Video controls at bottom
        control_layout = QVBoxLayout()

        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.valueChanged.connect(self.slider_moved)
        control_layout.addWidget(self.timeline_slider)

        # Playback controls
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

        # ===== RIGHT PANEL =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Events list 
        right_layout.addWidget(QLabel("Events:"))
        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(200)  # Limit height for 5-6 items
        self.events_list.itemClicked.connect(self.select_event)
        self.events_list.itemDoubleClicked.connect(self.jump_to_event)
        right_layout.addWidget(self.events_list)

        # Event controls
        event_controls = QVBoxLayout()

        # Button row 1
        button_row1 = QHBoxLayout()
        self.new_event_btn = QPushButton("New Event")
        self.new_event_btn.clicked.connect(self.new_event)
        button_row1.addWidget(self.new_event_btn)

        # Button row 2
        button_row2 = QHBoxLayout()
        self.mark_start_btn = QPushButton("Mark Start")
        self.mark_start_btn.clicked.connect(self.mark_start)
        self.mark_end_btn = QPushButton("Mark End")
        self.mark_end_btn.clicked.connect(self.mark_end)
        button_row2.addWidget(self.mark_start_btn)
        button_row2.addWidget(self.mark_end_btn)

        # Button row 3
        button_row3 = QHBoxLayout()
        self.delete_event_btn = QPushButton("Delete Event")
        self.delete_event_btn.clicked.connect(self.delete_event)
        self.save_events_btn = QPushButton("Save Events")
        self.save_events_btn.clicked.connect(self.save_events)
        button_row3.addWidget(self.delete_event_btn)
        button_row3.addWidget(self.save_events_btn)

        # Add all button rows
        event_controls.addLayout(button_row1)
        event_controls.addLayout(button_row2)
        event_controls.addLayout(button_row3)

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

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def setup_shortcuts(self):
        # Ctrl+Z for undo
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_action)
        
        # Ctrl+S for save
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_events)

    def open_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not dir_path:
            return

        self.video_paths.clear()
        self.video_list.clear()

        video_entries = []

        # Find all subdirectories with worldCamera.mp4
        for entry in os.scandir(dir_path):
            if entry.is_dir():
                video_path = os.path.join(entry.path, "worldCamera.mp4")
                if os.path.exists(video_path):
                    # self.video_paths.append(video_path)
                    # self.video_list.addItem(os.path.basename(entry.path))
                    # Store both the video path and display name in a list
                    display_name = f"{os.path.basename(entry.path)}"
                    video_entries.append((video_path, display_name))

        # Sort video entries by the directory and subdirectory names
        video_entries.sort(key=lambda x: x[0])  # Sort by file path

        # Add sorted items to video_paths and video_list
        for video_path, display_name in video_entries:
            self.video_paths.append(video_path)
            self.video_list.addItem(display_name)


    def select_video(self, item):
        index = self.video_list.row(item)
        if 0 <= index < len(self.video_paths):
            # load_video will check for unsaved changes
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
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
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
        # Check for unsaved changes before loading a new video
        if self.cap is not None and not self.check_unsaved_changes():
            return

        # Clean up existing video
        if self.cap is not None:
            self.cap.release()
            self.timer.stop()

        self.current_video_index = index
        self.events.clear()
        self.events_list.clear()
        self.selected_event = None
        self.event_history.clear()  # Clear undo history
        self.frame_to_gaze = {}  # Clear gaze data
        self.has_unsaved_changes = False  # Reset unsaved changes flag

        # Open the new video
        video_path = self.video_paths[index]
        video_dir = os.path.dirname(video_path)
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            self.video_label.setText(f"Error opening video: {video_path}")
            return

        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.playing = False
        self.play_btn.setText("Play")

        # Update timeline slider
        self.timeline_slider.setMaximum(self.total_frames - 1)
        self.timeline_slider.setValue(0)

        # Load gaze data if available
        gaze_path = os.path.join(video_dir, "gazeData.tsv")
        if os.path.exists(gaze_path):
            try:
                self.load_gaze_data(gaze_path)
            except Exception as e:
                print(f"Error loading gaze data: {e}")

        # Update UI
        self.display_frame()

        # Look for existing annotations
        csv_path = os.path.splitext(video_path)[0] + "_events.csv"
        if os.path.exists(csv_path):
            self.load_events(csv_path)
            # Save initial state for undo
            self.save_event_state()

    def load_gaze_data(self, gaze_path):
        """Load gaze data from TSV file and organize by frame index"""
        # Load the gaze data
        self.gaze_data = pd.read_csv(gaze_path, sep="\t")

        # Create a dictionary mapping frame indices to gaze points
        self.frame_to_gaze = {}

        for _, row in self.gaze_data.iterrows():
            frame_idx = int(row["frame_idx"])

            # Skip if gaze coordinates are missing
            if pd.isna(row["gaze_pos_vid_x"]) or pd.isna(row["gaze_pos_vid_y"]):
                continue
            x = float(row["gaze_pos_vid_x"])
            y = float(row["gaze_pos_vid_y"])

            # Add gaze point to the frame
            if frame_idx not in self.frame_to_gaze:
                self.frame_to_gaze[frame_idx] = []

            self.frame_to_gaze[frame_idx].append((x, y))

    def jump_to_event(self, item):
        """Jump to the start or end of the selected event when double-clicked"""
        index = self.events_list.row(item)
        if 0 <= index < len(self.events):
            event = self.events[index]

            # Check if Shift key is pressed for end frame
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                # Jump to end frame if defined
                if event["end"] != -1:
                    self.current_frame = event["end"]
                    self.display_frame()
            else:
                # Jump to start frame if defined, otherwise end frame
                if event["start"] != -1:
                    self.current_frame = event["start"]
                    self.display_frame()
                elif event["end"] != -1:
                    self.current_frame = event["end"]
                    self.display_frame()

    def display_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        # Set frame position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            return

        # Add gaze points if available for this frame
        if self.current_frame in self.frame_to_gaze:
            for x, y in self.frame_to_gaze[self.current_frame]:
                h, w = frame.shape[:2]
                # Draw green dot for gaze point (ensure coordinates are within image bounds)
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(
                        frame, (int(x), int(y)), 5, (0, 255, 0), -1
                    )  # Green dot, radius 5, filled

        # Check if current frame is within any event, and add purple border if it is
        frame_in_event = False
        for event in self.events:
            if (event["start"] != -1 and event["end"] != -1 and 
                event["start"] <= self.current_frame <= event["end"]):
                frame_in_event = True
                break
        
        # Add purple border if frame is in an event
        if frame_in_event:
            h, w = frame.shape[:2]
            border_thickness = 1
            frame = cv2.copyMakeBorder(
                frame, 
                border_thickness, border_thickness, border_thickness, border_thickness, 
                cv2.BORDER_CONSTANT, 
                value=(123, 171, 61) 
            )

        # Convert frame to format suitable for Qt
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, w * ch, QImage.Format.Format_RGB888)

        # Display frame
        self.video_label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        )

        # Update frame info and slider
        self.frame_info.setText(
            f"Frame: {self.current_frame + 1} / {self.total_frames}"
        )

        # Update slider without triggering valueChanged
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(self.current_frame)
        self.timeline_slider.blockSignals(False)

    def slider_moved(self):
        if self.cap is None or not self.cap.isOpened():
            return

        self.current_frame = self.timeline_slider.value()
        self.display_frame()

    def next_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.display_frame()
        else:
            # End of video
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
        # Create a deep copy of the events list
        state_copy = []
        for event in self.events:
            state_copy.append(event.copy())
        self.event_history.append(state_copy)

        # Limit history size to prevent memory issues
        if len(self.event_history) > 20:
            self.event_history.pop(0)

    def undo_action(self):
        """Undo the last event-related action"""
        if not self.event_history:
            return

        # Save event selected state
        prev_selected = self.selected_event

        # Restore previous state
        self.events = self.event_history.pop()
        
        # Mark as having unsaved changes
        if self.events:
            self.has_unsaved_changes = True

        # Update UI
        self.update_event_list()

        # Restore selection if possible
        if prev_selected is not None and prev_selected < len(self.events):
            self.selected_event = prev_selected
            self.events_list.setCurrentRow(prev_selected)
        else:
            self.selected_event = None

    def new_event(self):
        if self.cap is None:
            QMessageBox.warning(self, "Warning", "Please load a video first.")
            return

        # Check if there's already an incomplete event
        for i, event in enumerate(self.events):
            if event["start"] == -1 or event["end"] == -1:
                QMessageBox.warning(
                    self,
                    "Incomplete Event",
                    f"{event['name']} is incomplete. Please complete it before creating a new event.",
                )
                # Select the incomplete event
                self.selected_event = i
                self.events_list.setCurrentRow(i)
                return

        # Save current state for undo
        self.save_event_state()

        # Create new event with automatically assigned number
        event_number = len(self.events) + 1
        event = {"name": f"Event {event_number}", "start": -1, "end": -1}
        self.events.append(event)
        self.selected_event = len(self.events) - 1
        self.has_unsaved_changes = True
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

        # Save current state for undo
        self.save_event_state()

        # Check if this would create an invalid state
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

        # Save current state for undo
        self.save_event_state()

        # Check if this would create an invalid state
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
            # Save current state for undo
            self.save_event_state()

            self.events.pop(self.selected_event)

            # Renumber all events
            for i, event in enumerate(self.events):
                event["name"] = f"Event {i+1}"

            # Update selection
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

        # Select current event in the list
        if self.selected_event is not None:
            self.events_list.setCurrentRow(self.selected_event)

    def save_events(self):
        if self.cap is None or self.current_video_index < 0:
            return

        video_path = self.video_paths[self.current_video_index]
        csv_path = os.path.splitext(video_path)[0] + "_events.csv"

        try:
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Event", "Start Frame", "End Frame"])

                for event in self.events:
                    writer.writerow([event["name"], event["start"], event["end"]])

            self.has_unsaved_changes = False
            QMessageBox.information(self, "Success", f"Events saved to {csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save events: {str(e)}")

    def load_events(self, csv_path):
        self.events.clear()

        try:
            with open(csv_path, "r") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header

                for i, row in enumerate(reader):
                    if len(row) >= 3:
                        event = {
                            "name": f"Event {i+1}",  # Force consistent naming
                            "start": (
                                int(row[1])
                                if row[1] != "-1" and row[1] != "N/A"
                                else -1
                            ),
                            "end": (
                                int(row[2])
                                if row[2] != "-1" and row[2] != "N/A"
                                else -1
                            ),
                        }
                        self.events.append(event)

            # Reset unsaved changes flag since we just loaded from disk
            self.has_unsaved_changes = False
            
            self.update_event_list()

            # Set first event as selected if available
            if self.events:
                self.selected_event = 0
                self.events_list.setCurrentRow(0)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading events: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        modifiers = event.modifiers()
        
        if event.key() == Qt.Key.Key_Right:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                # Jump 10 frames forward with Shift+Right
                for _ in range(10):
                    if self.current_frame < self.total_frames - 1:
                        self.current_frame += 1
                    else:
                        break
                self.display_frame()
            else:
                self.next_frame()
        elif event.key() == Qt.Key.Key_Left:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                # Jump 10 frames backward with Shift+Left
                for _ in range(10):
                    if self.current_frame > 0:
                        self.current_frame -= 1
                    else:
                        break
                self.display_frame()
            else:
                self.prev_frame()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # Check for unsaved changes before closing
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save them before exiting?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_events()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # Clean up resources
        if self.cap is not None:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoAnnotator()
    player.show()
    sys.exit(app.exec())
