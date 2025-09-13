"""Pupil size visualization widget."""

import warnings

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph import PlotWidget
from scipy.ndimage import gaussian_filter1d

from ..core.color_theme_manager import ColorThemeManager

# Plot styling constants
BACKGROUND_COLOR = "#2b2b2b"
TICK_SPACING_MAJOR = 1
TICK_SPACING_MINOR = 1
GRID_ALPHA = 0.1
GAUSSIAN_FILTER_SIGMA = 3
PLOT_PEN_COLOR = "#8B7AA2"
PLOT_PEN_WIDTH = 2.5
Y_RANGE_PADDING = 0.1
EVENT_ALPHA = 50


class PupilSizePlot(PlotWidget):
    """Custom PyQtGraph widget for pupil size visualization."""

    def __init__(self, parent: PlotWidget | None = None) -> None:
        """Initialize the pupil size plot widget."""
        super().__init__(parent)
        self.color_manager = ColorThemeManager()

        # Plot styling setup
        self.setBackground(BACKGROUND_COLOR)
        self.getPlotItem().hideAxis("bottom")
        left_axis = self.getPlotItem().getAxis("left")
        left_axis.setTextPen("white")
        left_axis.enableAutoSIPrefix(False)
        left_axis.setTickSpacing(major=TICK_SPACING_MAJOR, minor=TICK_SPACING_MINOR)
        self.getPlotItem().showGrid(y=True, alpha=GRID_ALPHA)

        # Disable mouse interactions
        self.getPlotItem().setMouseEnabled(x=False, y=False)
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().hideButtons()

        self.pupil_data = None
        self.frame_data = None
        self.smoothed_pupil_data = None
        self.total_frames = 0
        self.events = []
        self.plot_curve = None
        self.event_regions = []

        self.setup_empty_plot()

    def setup_empty_plot(self) -> None:
        """Setup empty plot state."""
        self.clear()
        self.getPlotItem().hideAxis("left")
        self.smoothed_pupil_data = None
        self.plot_curve = None
        self.event_regions = []

    def update_data(
        self, gaze_data: pd.DataFrame, total_frames: int, events: list[dict[str, any]] | None = None
    ) -> None:
        """Update plot with new gaze data."""
        self.total_frames = total_frames
        self.events = events or []

        new_data = gaze_data is not None and (
            not hasattr(self, "current_gaze_data") or self.current_gaze_data is not gaze_data
        )

        if gaze_data is not None and "pup_diam_r" in gaze_data.columns and "pup_diam_l" in gaze_data.columns:
            if new_data:
                # Process pupil diameter data
                self.current_gaze_data = gaze_data
                self.frame_data = gaze_data["frame_idx"].to_numpy()
                pup_diam_r = gaze_data["pup_diam_r"].to_numpy()
                pup_diam_l = gaze_data["pup_diam_l"].to_numpy()

                if len(pup_diam_r) > 0 and len(pup_diam_l) > 0:
                    # Average left and right pupil diameters
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        self.pupil_data = np.nanmean([pup_diam_r, pup_diam_l], axis=0)
                else:
                    self.pupil_data = np.array([])

                # Remove invalid data points
                valid_mask = ~np.isnan(self.pupil_data)
                self.frame_data = self.frame_data[valid_mask]
                self.pupil_data = self.pupil_data[valid_mask]

                # Apply smoothing filter
                self.smoothed_pupil_data = gaussian_filter1d(self.pupil_data, sigma=GAUSSIAN_FILTER_SIGMA)

            self.plot_data()
        else:
            self.clear_plot()

    def plot_data(self) -> None:
        """Plot pupil data with events overlay."""
        self.clear()

        if self.pupil_data is not None and len(self.pupil_data) > 0:
            self.getPlotItem().showAxis("left")
            self.event_regions = []

            if self.events:
                for event in self.events:
                    if event["start"] != -1 and event["end"] != -1:
                        color = self._get_event_color(event["name"])
                        region = pg.LinearRegionItem(
                            [event["start"], event["end"]], brush=color, pen="transparent", movable=False
                        )
                        region.lines[0].hide()
                        region.lines[1].hide()
                        self.addItem(region)
                        self.event_regions.append(region)

            pen = pg.mkPen(color=PLOT_PEN_COLOR, width=PLOT_PEN_WIDTH)
            self.plot_curve = self.plot(self.frame_data, self.smoothed_pupil_data, pen=pen, antialias=True)

            self.setXRange(0, self.total_frames, padding=0)
            self.setYRange(np.min(self.smoothed_pupil_data), np.max(self.smoothed_pupil_data), padding=Y_RANGE_PADDING)

    def clear_plot(self) -> None:
        """Clear the plot."""
        self.setup_empty_plot()

    def _get_event_color(self, event_name: str) -> tuple[int, int, int, int]:
        rgb_color = self.color_manager.get_color(event_name)
        return (rgb_color[0], rgb_color[1], rgb_color[2], EVENT_ALPHA)
