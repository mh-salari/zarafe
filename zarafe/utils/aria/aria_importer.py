"""Handles importing of Meta Aria Gen 1 VRS recordings."""

import logging
from pathlib import Path

import pandas as pd
from glassesTools import video_utils
from projectaria_tools.core import data_provider
from PyQt6.QtWidgets import QApplication

from .aria_vrs_exporter import (
    check_required_streams,
    export_camera_video,
    export_gaze_data_and_calibration,
    export_imu_data,
    export_local_gaze_data,
    export_metadata,
    print_camera_timing_info,
)

logger = logging.getLogger(__name__)


class AriaRecording:
    """Represents a Meta Aria Gen 1 recording discovered in a directory."""

    def __init__(self, vrs_path: Path, local_gaze_csv_path: Path | None = None) -> None:
        """Initialize an Aria recording.

        Args:
            vrs_path: Path to the VRS file
            local_gaze_csv_path: Optional path to local gaze CSV file

        """
        self.source_path = vrs_path
        self.name = vrs_path.stem
        self.eye_tracker = "Meta Aria Gen 1"
        self.participant = None
        self.working_directory = None
        self.local_gaze_csv_path = local_gaze_csv_path

        # Try to extract participant info from filename or metadata
        self._extract_participant_info()

    def _extract_participant_info(self) -> None:
        """Extract participant information from filename if available."""
        # You can customize this based on your naming convention
        # For now, we'll leave it as None and let the user handle it


def discover_aria_recordings(search_dir: Path) -> list[AriaRecording]:
    """Discover Aria VRS recordings in a directory.

    Args:
        search_dir: Directory to search for VRS files

    Returns:
        List of AriaRecording objects found in the directory

    """
    recordings = []

    # Look for .vrs files
    for vrs_file in search_dir.glob("*.vrs"):
        try:
            # Verify it's a valid VRS file by trying to open it
            provider = data_provider.create_vrs_data_provider(str(vrs_file))
            if provider:
                # Check for local gaze CSV file with pattern: {stem}_local_gaze.csv
                local_gaze_csv = vrs_file.parent / f"{vrs_file.stem}_local_gaze.csv"
                if not local_gaze_csv.exists():
                    local_gaze_csv = None
                else:
                    logger.info("Found local gaze CSV: %s", local_gaze_csv.name)

                recordings.append(AriaRecording(vrs_file, local_gaze_csv_path=local_gaze_csv))
                logger.info("Found Aria recording: %s", vrs_file.name)
        except Exception as e:
            logger.warning("Failed to open VRS file %s: %s", vrs_file, e)
            continue

    return recordings


def import_aria_recording(rec: AriaRecording, output_dir: Path, progress_dialog: object = None) -> bool:
    """Import an Aria recording using the VRS exporter.

    Args:
        rec: AriaRecording object to import
        output_dir: Directory where the recording will be imported
        progress_dialog: Optional progress dialog to check for cancellation

    Returns:
        True if import was successful, False otherwise

    """

    def check_cancelled() -> bool:
        """Check if user cancelled and process events."""
        if progress_dialog:
            QApplication.processEvents()
            if progress_dialog.wasCanceled():
                logger.info("Import of %s cancelled by user", rec.name)
                return True
        return False

    def raise_provider_error() -> None:
        """Raise error for failed VRS data provider creation."""
        raise RuntimeError(f"Failed to create VRS data provider for {rec.source_path}")

    try:
        # Create output directory
        output_dir.mkdir(exist_ok=True, parents=True)

        # Check which files already exist
        existing_files = {
            "worldCamera": (output_dir / "worldCamera.mp4").exists(),
            "eyeCamera": (output_dir / "eyeCamera.avi").exists(),
            "gazeData": (output_dir / "gazeData.tsv").exists(),
            "gazeData_local": (output_dir / "gazeData_local.tsv").exists(),
            "imu": (output_dir / "imu_right.csv").exists() and (output_dir / "imu_left.csv").exists(),
            "metadata": (output_dir / "metadata.json").exists(),
            "calibration": (output_dir / "calibration.xml").exists(),
        }

        if all(existing_files.values()):
            logger.info("All files for %s already exist, skipping import", rec.name)
            return True

        logger.info("Importing Aria recording %s to %s", rec.name, output_dir)

        # Create VRS data provider
        if progress_dialog:
            progress_dialog.setLabelText(f"Loading VRS file: {rec.name}")
            QApplication.processEvents()

        vrs_data_provider = data_provider.create_vrs_data_provider(str(rec.source_path))
        if not vrs_data_provider:
            raise_provider_error()

        if check_cancelled():
            return False

        # Check for required streams
        has_rgb_camera, has_eye_tracking_camera, rgb_stream_id, eye_tracking_stream_id = check_required_streams(
            vrs_data_provider, skip_rgb=False, skip_eye=False
        )

        # Get camera timing information
        rgb_start_time_ns, rgb_end_time_ns, eye_tracking_start_time_ns, eye_tracking_end_time_ns = (
            print_camera_timing_info(vrs_data_provider, rgb_stream_id, eye_tracking_stream_id)
        )

        # Get camera configurations
        rgb_camera_config = vrs_data_provider.get_image_configuration(rgb_stream_id)
        eye_tracking_camera_config = vrs_data_provider.get_image_configuration(eye_tracking_stream_id)

        if check_cancelled():
            return False

        # Export RGB camera video
        if has_rgb_camera and not existing_files["worldCamera"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Extracting RGB camera video: {rec.name}")
                QApplication.processEvents()
            logger.info("Extracting RGB camera video...")
            export_camera_video(
                rec.source_path, output_dir, rgb_stream_id, "worldCamera.mp4", vrs_data_provider=vrs_data_provider
            )
        elif existing_files["worldCamera"]:
            logger.info("RGB camera video already exists, skipping")

        if check_cancelled():
            return False

        # Export eye tracking camera video (lossless)
        if has_eye_tracking_camera and not existing_files["eyeCamera"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Extracting eye camera video: {rec.name}")
                QApplication.processEvents()
            logger.info("Extracting eye tracking camera video (lossless)...")
            export_camera_video(
                rec.source_path,
                output_dir,
                eye_tracking_stream_id,
                "eyeCamera.avi",
                use_lossless=True,
                vrs_data_provider=vrs_data_provider,
            )
        elif existing_files["eyeCamera"]:
            logger.info("Eye camera video already exists, skipping")

        if check_cancelled():
            return False

        # Export gaze data and calibration
        # Check for both MPS data and local gaze CSV
        mps_folder_path = rec.source_path.parent / f"mps_{rec.source_path.stem}_vrs"
        has_mps_data = mps_folder_path.exists()
        has_local_gaze = rec.local_gaze_csv_path is not None and rec.local_gaze_csv_path.exists()

        if has_mps_data and not existing_files["gazeData"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Extracting MPS gaze data: {rec.name}")
                QApplication.processEvents()
            logger.info("Extracting MPS gaze data and calibration...")
            export_gaze_data_and_calibration(
                vrs_data_provider,
                rgb_stream_id,
                mps_folder_path,
                output_dir,
                rgb_start_time_ns,
                apply_upright_rotation=True,
            )
        elif existing_files["gazeData"]:
            logger.info("MPS gaze data already exists, skipping")
        elif not has_mps_data:
            logger.warning("MPS folder not found at %s, skipping MPS gaze data export", mps_folder_path)

        if has_local_gaze and not existing_files["gazeData_local"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Extracting local gaze data: {rec.name}")
                QApplication.processEvents()
            logger.info("Extracting local gaze data from %s...", rec.local_gaze_csv_path.name)

            export_local_gaze_data(
                vrs_data_provider,
                rgb_stream_id,
                rec.local_gaze_csv_path,
                output_dir,
                rgb_start_time_ns,
                apply_upright_rotation=True,
            )
        elif existing_files["gazeData_local"]:
            logger.info("Local gaze data already exists, skipping")

        if check_cancelled():
            return False

        # Export IMU data
        if not existing_files["imu"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Extracting IMU data: {rec.name}")
                QApplication.processEvents()
            logger.info("Extracting IMU data...")
            export_imu_data(vrs_data_provider, output_dir)
        else:
            logger.info("IMU data already exists, skipping")

        if check_cancelled():
            return False

        # Export metadata
        if not existing_files["metadata"]:
            if progress_dialog:
                progress_dialog.setLabelText(f"Exporting metadata: {rec.name}")
                QApplication.processEvents()
            logger.info("Exporting metadata...")
            export_metadata(
                vrs_data_provider,
                rec.source_path,
                output_dir,
                rgb_camera_config,
                eye_tracking_camera_config,
                rgb_start_time_ns,
                rgb_end_time_ns,
                eye_tracking_start_time_ns,
                eye_tracking_end_time_ns,
            )
        else:
            logger.info("Metadata already exists, skipping")

        if check_cancelled():
            return False

        # Post-process gaze data: add frame_idx column using glassesTools method
        # Get video frame timestamps (used for both MPS and local gaze data)
        video_path = output_dir / "worldCamera.mp4"
        frame_timestamps = None

        # Process MPS gaze data
        gaze_file = output_dir / "gaze.tsv"
        if gaze_file.exists():
            if progress_dialog:
                progress_dialog.setLabelText(f"Processing MPS gaze data: {rec.name}")
                QApplication.processEvents()
            logger.info("Adding frame_idx to MPS gaze data...")

            # Read gaze data
            gaze_data = pd.read_csv(gaze_file, sep="\t")

            # Get video frame timestamps
            if frame_timestamps is None:
                frame_timestamps = video_utils.get_frame_timestamps_from_video(video_path)

            # Convert gaze timestamps from microseconds to milliseconds
            gaze_data.loc[:, "timestamp"] /= 1000.0

            # Add frame_idx using glassesTools' method
            frame_idx_df = video_utils.timestamps_to_frame_number(
                gaze_data.loc[:, "timestamp"].values, frame_timestamps["timestamp"].values
            )
            gaze_data.insert(1, "frame_idx", frame_idx_df["frame_idx"].values)

            # Save as gazeData.tsv (the name zarafe expects)
            gaze_output_path = output_dir / "gazeData.tsv"
            gaze_data.to_csv(gaze_output_path, sep="\t", float_format="%.8f", index=False, na_rep="nan")

            # Remove the old gaze.tsv file
            gaze_file.unlink()

            logger.info("MPS gaze data with frame_idx saved to %s", gaze_output_path)

        # Process local gaze data
        local_gaze_file = output_dir / "gaze_local.tsv"
        if local_gaze_file.exists():
            if progress_dialog:
                progress_dialog.setLabelText(f"Processing local gaze data: {rec.name}")
                QApplication.processEvents()
            logger.info("Adding frame_idx to local gaze data...")

            # Read local gaze data
            local_gaze_data = pd.read_csv(local_gaze_file, sep="\t")

            # Get video frame timestamps if not already loaded
            if frame_timestamps is None:
                frame_timestamps = video_utils.get_frame_timestamps_from_video(video_path)

            # Convert gaze timestamps from microseconds to milliseconds
            local_gaze_data.loc[:, "timestamp"] /= 1000.0

            # Add frame_idx using glassesTools' method
            frame_idx_df = video_utils.timestamps_to_frame_number(
                local_gaze_data.loc[:, "timestamp"].values, frame_timestamps["timestamp"].values
            )
            local_gaze_data.insert(1, "frame_idx", frame_idx_df["frame_idx"].values)

            # Save as gazeData_local.tsv
            local_gaze_output_path = output_dir / "gazeData_local.tsv"
            local_gaze_data.to_csv(local_gaze_output_path, sep="\t", float_format="%.8f", index=False, na_rep="nan")

            # Remove the old gaze_local.tsv file
            local_gaze_file.unlink()

            logger.info("Local gaze data with frame_idx saved to %s", local_gaze_output_path)

        logger.info("Successfully imported Aria recording %s", rec.name)
        return True

    except Exception:
        logger.exception("Failed to import Aria recording %s", rec.name)
        return False
