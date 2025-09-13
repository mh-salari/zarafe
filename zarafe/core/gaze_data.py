"""Gaze data loading and processing."""

from pathlib import Path

import pandas as pd


class GazeDataManager:
    """Manages gaze data loading and frame mapping."""

    def __init__(self) -> None:
        """Initialize the gaze data manager."""
        self.gaze_data: pd.DataFrame | None = None
        self.frame_to_gaze: dict[int, list[tuple[float, float]]] = {}

    def load_gaze_data(self, gaze_path: Path) -> None:
        """Load gaze data from TSV file and organize by frame index."""
        self.gaze_data = pd.read_csv(str(gaze_path), sep="\t")
        self.frame_to_gaze = {}

        # Filter out rows with NaN gaze positions
        valid_data = self.gaze_data.dropna(subset=["gaze_pos_vid_x", "gaze_pos_vid_y"])

        for _, row in valid_data.iterrows():
            frame_idx = int(row["frame_idx"])
            x = float(row["gaze_pos_vid_x"])
            y = float(row["gaze_pos_vid_y"])

            self.frame_to_gaze.setdefault(frame_idx, []).append((x, y))

    def get_gaze_points(self, frame_idx: int) -> list[tuple[float, float]]:
        """Get gaze points for a specific frame."""
        return self.frame_to_gaze.get(frame_idx, [])

    def clear(self) -> None:
        """Clear all gaze data."""
        self.gaze_data = None
        self.frame_to_gaze = {}
