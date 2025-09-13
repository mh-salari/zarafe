"""File and path utilities."""

import os
from pathlib import Path

# File constants
VIDEO_FILENAME = "worldCamera.mp4"


def find_video_directories(base_dir: str) -> list[tuple[str, str]]:
    """Find all directories containing worldCamera.mp4 files."""
    video_entries = []

    for entry in os.scandir(base_dir):
        if entry.is_dir():
            video_path = Path(entry.path) / VIDEO_FILENAME
            if video_path.exists():
                display_name = Path(entry.path).name
                video_entries.append((str(video_path), display_name))

    return video_entries


def get_resource_path(filename: str) -> Path:
    """Get path to a resource file."""
    return Path(__file__).parent.parent.parent / "resources" / filename
