"""
Handles importing of eye-tracking data using glassesTools.
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

import pathvalidate
import glassesTools.importing
import glassesTools.eyetracker
from glassesTools.recording import Recording


def make_fs_dirname(rec_info: Recording, output_dir: Path = None) -> str:
    """
    Generates a filesystem-safe directory name for a recording.

    Args:
        rec_info: The Recording object.
        output_dir: The output directory to check for existing names.

    Returns:
        A unique, filesystem-safe directory name.
    """
    if rec_info.participant:
        dirname = f"{rec_info.eye_tracker.value}_{rec_info.participant}_{rec_info.name}"
    else:
        dirname = f"{rec_info.eye_tracker.value}_{rec_info.name}"

    # make sure its a valid path
    dirname = pathvalidate.sanitize_filename(dirname)

    # check it doesn't already exist
    if output_dir is not None:
        if (output_dir / dirname).is_dir():
            # add _1, _2, etc, until we find a unique name
            fver = 1
            while (output_dir / f"{dirname}_{fver}").is_dir():
                fver += 1
            dirname = f"{dirname}_{fver}"
    return dirname


def import_recordings(
    source_dir: Path,
    project_path: Path,
    device: glassesTools.eyetracker.EyeTracker,
    parent_widget=None,
) -> int:
    """
    Imports recordings from a source directory and its immediate subdirectories.

    Args:
        source_dir: The root directory to search for recordings.
        project_path: The path to the project where recordings will be imported.
        device: The eye tracker device model.
        parent_widget: The parent widget for dialogs.

    Returns:
        The number of successfully imported recordings.
    """
    # Build a list of directories to search: the source and its immediate children
    dirs_to_search = [source_dir]
    for item in source_dir.iterdir():
        if item.is_dir():
            dirs_to_search.append(item)

    all_recordings_to_import = []  # List of (rec_info, source_path) tuples

    # Discover recordings in all candidate directories
    for search_path in dirs_to_search:
        try:
            recs_info_list = glassesTools.importing.get_recording_info(source_dir=search_path, device=device)
            if recs_info_list:
                for rec_info in recs_info_list:
                    all_recordings_to_import.append((rec_info, search_path))
        except Exception:
            # Silently ignore directories that fail, as they may not be recordings
            continue

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
    for i, (rec_info, rec_source_dir) in enumerate(all_recordings_to_import):
        if progress.wasCanceled():
            break

        progress.setLabelText(f"Importing {rec_info.name} from {rec_source_dir.name}...")
        progress.setValue(i)
        QApplication.processEvents()

        try:
            rec_info.working_directory = project_path / make_fs_dirname(rec_info, project_path)

            glassesTools.importing.do_import(
                output_dir=None,  # Not needed when rec_info.working_directory is set
                source_dir=rec_source_dir,
                device=device,
                rec_info=rec_info,
                copy_scene_video=True,
            )
            successfully_imported += 1
        except Exception as e:
            QMessageBox.warning(
                parent_widget,
                "Import Error",
                f"Failed to import {rec_info.name}:\n{str(e)}",
            )

    progress.setValue(len(all_recordings_to_import))
    progress.close()

    return successfully_imported
