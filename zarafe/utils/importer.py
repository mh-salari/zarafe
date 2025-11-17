"""Handles importing of eye-tracking data using glassesTools."""

import logging
from pathlib import Path

import glassesTools.eyetracker
import glassesTools.importing
import pathvalidate
from glassesTools.recording import Recording
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from .aria import aria_importer

logger = logging.getLogger(__name__)


def make_fs_dirname(rec_info: Recording | aria_importer.AriaRecording, output_dir: Path | None = None) -> str:
    """Generates a filesystem-safe directory name for a recording.

    Args:
        rec_info: The Recording object (glassesTools or AriaRecording).
        output_dir: The output directory to check for existing names.

    Returns:
        A unique, filesystem-safe directory name.

    """
    # Handle both glassesTools Recording and AriaRecording
    if isinstance(rec_info, aria_importer.AriaRecording):
        eye_tracker_value = rec_info.eye_tracker
    else:
        eye_tracker_value = rec_info.eye_tracker.value

    if rec_info.participant:
        dirname = f"{eye_tracker_value} {rec_info.participant}_{rec_info.name}"
    else:
        dirname = f"{eye_tracker_value} {rec_info.name}"

    # make sure its a valid path
    dirname = pathvalidate.sanitize_filename(dirname)

    # check it doesn't already exist
    if output_dir is not None and (output_dir / dirname).is_dir():
        # add _1, _2, etc, until we find a unique name
        fver = 1
        while (output_dir / f"{dirname}_{fver}").is_dir():
            fver += 1
            dirname = f"{dirname}_{fver}"
    return dirname


def _get_search_directories(source_dir: Path) -> list[Path]:
    """Get list of directories to search for recordings."""
    dirs_to_search = [source_dir]
    for item in source_dir.iterdir():
        if item.is_dir():
            dirs_to_search.append(item)
    return dirs_to_search


def _discover_recordings(
    dirs_to_search: list[Path], device: glassesTools.eyetracker.EyeTracker, specific_files: list[Path] | None = None
) -> list[tuple]:
    """Discover all recordings in the given directories.

    Args:
        dirs_to_search: Directories to search for recordings
        device: Eye tracker device type
        specific_files: Optional list of specific files to import (for Aria VRS files)

    Returns:
        List of (recording_info, source_path) tuples

    """
    all_recordings_to_import = []

    # Handle Aria separately
    if device.value == "Meta Aria Gen 1":
        if specific_files:
            # Import only the specific VRS files selected by the user
            for vrs_file in specific_files:
                try:
                    # Check for local gaze CSV file
                    local_gaze_csv = vrs_file.parent / f"{vrs_file.stem}_local_gaze.csv"
                    if not local_gaze_csv.exists():
                        local_gaze_csv = None

                    aria_recording = aria_importer.AriaRecording(vrs_file, local_gaze_csv_path=local_gaze_csv)
                    all_recordings_to_import.append((aria_recording, vrs_file.parent))
                except Exception as e:
                    # Log and ignore files that fail
                    print(f"Warning: Failed to process VRS file {vrs_file}: {e}")
                    continue
        else:
            # Search directories for VRS files
            for search_path in dirs_to_search:
                try:
                    aria_recordings = aria_importer.discover_aria_recordings(search_path)
                    for rec_info in aria_recordings:
                        all_recordings_to_import.append((rec_info, search_path))
                except Exception as e:
                    # Log and ignore directories that fail
                    print(f"Warning: Failed to process directory {search_path}: {e}")
                    continue
    else:
        # Use glassesTools for other devices
        for search_path in dirs_to_search:
            try:
                recs_info_list = glassesTools.importing.get_recording_info(source_dir=search_path, device=device)
                if recs_info_list:
                    for rec_info in recs_info_list:
                        all_recordings_to_import.append((rec_info, search_path))
            except Exception as e:
                # Log and ignore directories that fail, as they may not be recordings
                print(f"Warning: Failed to process directory {search_path}: {e}")
                continue

    return all_recordings_to_import


def _import_single_recording(
    rec_info: object,
    rec_source_dir: Path,
    project_path: Path,
    device: glassesTools.eyetracker.EyeTracker,
    progress_dialog: object = None,
) -> bool:
    """Import a single recording and return success status."""
    try:
        rec_info.working_directory = project_path / make_fs_dirname(rec_info, project_path)

        # Handle Aria separately
        if device.value == "Meta Aria Gen 1":
            # Aria importer handles checking for existing files internally
            success = aria_importer.import_aria_recording(rec_info, rec_info.working_directory, progress_dialog)
            return 1 if success else 0
        # For other devices, skip if directory already exists
        if rec_info.working_directory.exists():
            logger.info("Recording directory '%s' already exists, skipping import.", rec_info.working_directory)
            return 2  # Skipped

        # Use glassesTools for other devices
        glassesTools.importing.do_import(
            output_dir=None,  # Not needed when rec_info.working_directory is set
            source_dir=rec_source_dir,
            device=device,
            rec_info=rec_info,
            copy_scene_video=True,
        )
        return 1  # Imported
    except Exception:  # Removed 'as e' as it's redundant with logger.exception
        logger.exception("Failed to import recording %s:", rec_info.name)
        return 0  # Failed


def import_recordings(
    source_dir: Path,
    project_path: Path,
    device: glassesTools.eyetracker.EyeTracker,
    parent_widget: object = None,
    specific_files: list[Path] | None = None,
) -> int:
    """Imports recordings from a source directory and its immediate subdirectories.

    Args:
        source_dir: The root directory to search for recordings.
        project_path: The path to the project where recordings will be imported.
        device: The eye tracker device model.
        parent_widget: The parent widget for dialogs.
        specific_files: Optional list of specific files to import (for Aria VRS files).

    Returns:
        The number of successfully imported recordings.

    """
    dirs_to_search = _get_search_directories(source_dir)
    all_recordings_to_import = _discover_recordings(dirs_to_search, device, specific_files)

    if not all_recordings_to_import:
        QMessageBox.warning(
            parent_widget,
            "No Recordings Found",
            f"No recordings for the selected eye tracker were found in '{source_dir.name}' or its subdirectories.",
        )
        return 0

    progress = QProgressDialog(
        "Importing recordings...",
        "Cancel",
        0,
        len(all_recordings_to_import),
        parent_widget,
    )
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.show()

    successfully_imported = 0
    skipped_recordings = 0
    failed_recordings = 0
    for i, (rec_info, rec_source_dir) in enumerate(all_recordings_to_import):
        if progress.wasCanceled():
            break
        progress.setLabelText(f"Importing {rec_info.name} from {rec_source_dir.name}...")
        progress.setValue(i)
        QApplication.processEvents()

        import_status = _import_single_recording(rec_info, rec_source_dir, project_path, device, progress)
        if import_status == 1:
            successfully_imported += 1
        elif import_status == 2:
            skipped_recordings += 1
        else:  # import_status == 0
            failed_recordings += 1
            QMessageBox.warning(
                parent_widget,
                "Import Error",
                f"Failed to import {rec_info.name}",
            )

    progress.setValue(len(all_recordings_to_import))
    progress.close()

    # Display summary message
    summary_message = f"Import complete.\nSuccessfully imported: {successfully_imported}"
    if skipped_recordings > 0:
        summary_message += f"\nSkipped (already existed): {skipped_recordings}"
    if failed_recordings > 0:
        summary_message += f"\nFailed: {failed_recordings}"

    QMessageBox.information(
        parent_widget,
        "Import Summary",
        summary_message,
    )

    return successfully_imported
