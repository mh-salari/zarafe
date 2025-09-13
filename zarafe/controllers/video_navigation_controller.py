"""Video navigation controller."""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem


class VideoNavigationController:
    """Manages video selection and navigation."""

    def __init__(self) -> None:
        """Initialize the video navigation controller."""
        self.current_video_index = -1
        self.video_paths = []

    def select_video(self, item: QListWidgetItem, video_list: QListWidget, load_video_callback: object) -> None:
        """Handle video selection from list."""
        index = video_list.row(item)
        self.current_video_index = index
        load_video_callback(index)

    def next_video(self, load_video_callback: object) -> None:
        """Navigate to next video."""
        if self.current_video_index < len(self.video_paths) - 1:
            self.current_video_index += 1
            load_video_callback(self.current_video_index)

    def prev_video(self, load_video_callback: object) -> None:
        """Navigate to previous video."""
        if self.current_video_index > 0:
            self.current_video_index -= 1
            load_video_callback(self.current_video_index)

    def set_video_paths(self, video_paths: list[str]) -> None:
        """Set available video paths."""
        self.video_paths = video_paths
        if not video_paths:
            self.current_video_index = -1

    def get_current_index(self) -> int:
        """Get current video index."""
        return self.current_video_index

    def set_current_index(self, index: int) -> None:
        """Set current video index."""
        if 0 <= index < len(self.video_paths):
            self.current_video_index = index
