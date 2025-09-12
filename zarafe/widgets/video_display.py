"""Video display and rendering component."""

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy

from ..core.config import ProjectConfig


class VideoDisplay:
    """Video display and rendering component."""

    def __init__(self, parent, config: ProjectConfig):
        self.parent = parent
        self.config = config
        self.setup_display()

    def setup_display(self) -> QLabel:
        """Setup video display label."""
        self.parent.video_label = QLabel("No video selected")
        self.parent.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parent.video_label.setMinimumSize(640, 480)
        self.parent.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Annotation overlay
        self.parent.annotation_info_label = QLabel("")
        self.parent.annotation_info_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.parent.annotation_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.parent.annotation_info_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.parent.annotation_info_label.setParent(self.parent.video_label)
        self.parent.annotation_info_label.hide()

        return self.parent.video_label

    def render_frame(self) -> None:
        """Render current frame with annotations and gaze data."""
        ret, frame = self.parent.video_manager.read_frame()
        if not ret:
            return

        # Add event border if in event
        frame_in_event, event_color, current_event = self.check_frame_in_event()
        if frame_in_event:
            frame = self.add_event_border(frame, event_color)
            if current_event:
                self.show_event_annotation(current_event, event_color)
        else:
            self.parent.annotation_info_label.hide()

        # Convert and scale frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        img = QImage(frame_rgb.data, w, h, w * ch, QImage.Format.Format_RGB888)

        scaled_pixmap = QPixmap.fromImage(img).scaled(
            self.parent.video_label.width(),
            self.parent.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        # Add gaze points
        scaled_pixmap = self.add_gaze_points(scaled_pixmap, w, h)

        self.parent.video_label.setPixmap(scaled_pixmap)

        # Update frame info
        current_frame = self.parent.video_manager.current_frame
        total_frames = self.parent.video_manager.total_frames
        self.parent.frame_info.setText(f"Frame: {current_frame + 1} / {total_frames}")

    def check_frame_in_event(self) -> tuple[bool, tuple[int, int, int] | None, dict | None]:
        """Check if current frame is within an event."""
        current_frame = self.parent.video_manager.current_frame + 1

        for event in self.parent.event_manager.events:
            if event["start"] != -1 and event["end"] != -1 and event["start"] <= current_frame <= event["end"]:
                rgb_color = self.config.get_color(event["name"])
                # Convert RGB to BGR for OpenCV
                bgr_color = (rgb_color[2], rgb_color[1], rgb_color[0])
                return True, bgr_color, event

        return False, None, None

    def add_event_border(self, frame, event_color: tuple[int, int, int]):
        """Add colored border to frame."""
        return cv2.copyMakeBorder(frame, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=event_color)

    def show_event_annotation(self, event: dict, event_color: tuple[int, int, int]) -> None:
        """Show event annotation overlay."""
        duration = self.parent.video_manager.calculate_duration(event["start"], event["end"])
        duration_str = f"{duration}s" if duration is not None else "N/A"

        if self.config.is_marker_interval_event(event["name"]):
            annotation_text = f"{event['name']} ({duration_str})"
        else:
            event_parts = event["name"].split()
            if len(event_parts) >= 2:
                event_type = event_parts[0]
                target = event_parts[-1]
                annotation_text = f"{event_type} {target} ({duration_str})"
            else:
                annotation_text = f"{event['name']} ({duration_str})"

        color_hex = f"#{event_color[2]:02x}{event_color[1]:02x}{event_color[0]:02x}"

        self.parent.annotation_info_label.setText(annotation_text)
        self.parent.annotation_info_label.setStyleSheet(f"color: {color_hex}; font-size: 14px; font-weight: bold;")
        self.parent.annotation_info_label.adjustSize()
        self.position_annotation_overlay()
        self.parent.annotation_info_label.show()

    def add_gaze_points(self, pixmap: QPixmap, original_w: int, original_h: int) -> QPixmap:
        """Add gaze points to the pixmap."""
        gaze_points = self.parent.gaze_manager.get_gaze_points(self.parent.video_manager.current_frame)
        if not gaze_points:
            return pixmap

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale_x = pixmap.width() / original_w
        scale_y = pixmap.height() / original_h

        for x, y in gaze_points:
            if 0 <= x < original_w and 0 <= y < original_h:
                scaled_x = int(x * scale_x)
                scaled_y = int(y * scale_y)

                painter.setPen(QPen(QColor(0, 255, 0, 150), 1))
                painter.setBrush(QBrush(QColor(0, 255, 0, 150)))
                painter.drawEllipse(scaled_x - 2, scaled_y - 2, 4, 4)

        painter.end()
        return pixmap

    def position_annotation_overlay(self) -> None:
        """Position the annotation overlay correctly on the video."""
        if not self.parent.video_label.pixmap():
            return

        label_size = self.parent.video_label.size()
        pixmap_size = self.parent.video_label.pixmap().size()

        # Calculate scaling and position
        scale_x = label_size.width() / pixmap_size.width()
        scale_y = label_size.height() / pixmap_size.height()
        scale = min(scale_x, scale_y)

        display_width = int(pixmap_size.width() * scale)
        display_height = int(pixmap_size.height() * scale)

        offset_x = (label_size.width() - display_width) // 2
        offset_y = (label_size.height() - display_height) // 2

        self.parent.annotation_info_label.move(offset_x + 10, offset_y + 10)
