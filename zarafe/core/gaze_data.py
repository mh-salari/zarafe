"""Gaze data loading and processing."""

from pathlib import Path

import pandas as pd


class GazeDataManager:
    """Manages gaze data loading and frame mapping."""

    def __init__(self) -> None:
        """Initialize the gaze data manager."""
        self.gaze_data: pd.DataFrame | None = None
        self.gaze_data_local: pd.DataFrame | None = None
        self.frame_to_gaze: dict[int, list[tuple[float, float]]] = {}
        self.frame_to_gaze_local: dict[int, list[tuple[float, float]]] = {}

    def load_gaze_data(self, gaze_path: Path) -> None:
        """Load gaze data from TSV file and organize by frame index.

        Also checks for local gaze data file (gazeData_local.tsv).
        If gaze_path doesn't exist, still tries to load local gaze data.
        """
        # Load primary gaze data if it exists
        if gaze_path.exists():
            self.gaze_data = pd.read_csv(str(gaze_path), sep="\t")
            self.frame_to_gaze = {}

            # Filter out rows with NaN gaze positions
            valid_data = self.gaze_data.dropna(subset=["gaze_pos_vid_x", "gaze_pos_vid_y"])

            for _, row in valid_data.iterrows():
                frame_idx = int(row["frame_idx"])
                x = float(row["gaze_pos_vid_x"])
                y = float(row["gaze_pos_vid_y"])

                self.frame_to_gaze.setdefault(frame_idx, []).append((x, y))
        else:
            self.gaze_data = None
            self.frame_to_gaze = {}

        # Load local gaze data if available
        local_gaze_path = gaze_path.parent / "gazeData_local.tsv"
        if local_gaze_path.exists():
            self.gaze_data_local = pd.read_csv(str(local_gaze_path), sep="\t")
            self.frame_to_gaze_local = {}

            # Filter out rows with NaN gaze positions
            valid_data_local = self.gaze_data_local.dropna(subset=["gaze_pos_vid_x", "gaze_pos_vid_y"])

            for _, row in valid_data_local.iterrows():
                frame_idx = int(row["frame_idx"])
                x = float(row["gaze_pos_vid_x"])
                y = float(row["gaze_pos_vid_y"])

                self.frame_to_gaze_local.setdefault(frame_idx, []).append((x, y))
        else:
            self.gaze_data_local = None
            self.frame_to_gaze_local = {}

    def get_gaze_points(self, frame_idx: int) -> list[tuple[float, float]]:
        """Get gaze points for a specific frame (primary gaze data)."""
        return self.frame_to_gaze.get(frame_idx, [])

    def get_gaze_points_local(self, frame_idx: int) -> list[tuple[float, float]]:
        """Get local gaze points for a specific frame."""
        return self.frame_to_gaze_local.get(frame_idx, [])

    def clear(self) -> None:
        """Clear all gaze data."""
        self.gaze_data = None
        self.gaze_data_local = None
        self.frame_to_gaze = {}
        self.frame_to_gaze_local = {}
