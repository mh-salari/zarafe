"""Video playback and management."""

import cv2
from PyQt6.QtCore import QTimer

from .audio_manager import AudioManager


class VideoManager:
    """Manages video loading, playback, and frame navigation."""

    def __init__(self) -> None:
        """Initialize the video manager."""
        self.cap: cv2.VideoCapture | None = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0.0
        self.playing = False
        self.last_frame_read = -1

        self.timer = QTimer()
        self.frame_callback = None
        self.audio_manager = AudioManager()

    def load_video(self, video_path: str) -> bool:
        """Load a video file."""
        self.release()

        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.last_frame_read = -1
        self.playing = False

        self.audio_manager.load_video(video_path)

        return True

    def read_frame(self) -> tuple[bool, any]:
        """Read the current frame, optimizing for sequential reads."""
        if self.current_frame != self.last_frame_read + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        ret, frame = self.cap.read()
        if ret:
            self.last_frame_read = self.current_frame

        return ret, frame

    def next_frame(self) -> bool:
        """Move to next frame."""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            return True
        return False

    def prev_frame(self) -> bool:
        """Move to previous frame."""
        if self.current_frame > 0:
            self.current_frame -= 1
            return True
        return False

    def jump_frames(self, offset: int) -> None:
        """Jump by offset frames."""
        self.current_frame = max(0, min(self.current_frame + offset, self.total_frames - 1))
        self.last_frame_read = -1

    def set_frame(self, frame_number: int) -> None:
        """Set current frame to specific number."""
        self.current_frame = max(0, min(frame_number, self.total_frames - 1))
        self.last_frame_read = -1

        position_ms = int((self.current_frame / self.fps) * 1000)
        self.audio_manager.set_position(position_ms)

    def toggle_playback(self) -> bool:
        """Toggle play/pause state."""
        self.playing = not self.playing
        return self.playing

    def start_playback(self, frame_callback: object) -> None:
        """Start playback with callback."""
        if self.playing:
            if self.frame_callback != frame_callback:
                if self.frame_callback is not None:
                    self.timer.timeout.disconnect()
                self.timer.timeout.connect(frame_callback)
                self.frame_callback = frame_callback

            interval = int(1000 / self.fps)
            self.timer.start(interval)

            self.audio_manager.play()

    def stop_playback(self) -> None:
        """Stop playback."""
        self.timer.stop()
        self.playing = False

        self.audio_manager.pause()

    def calculate_duration(self, start_frame: int, end_frame: int) -> float | None:
        """Calculate duration in seconds from frame numbers."""
        if start_frame == -1 or end_frame == -1:
            return None
        return round((end_frame - start_frame + 1) / self.fps, 1)

    def release(self) -> None:
        """Release video resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.timer.stop()

        self.audio_manager.cleanup()
