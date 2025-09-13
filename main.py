"""Zarafe - Video annotation tool for eye tracking studies."""

import os
import sys

# Suppress Qt multimedia debug output - must be set before Qt imports
os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"

# Patch ffmpeg module before any other imports that might use it
from zarafe.utils import ffmpeg_compat  # noqa: F401 I001

from PyQt6.QtWidgets import QApplication

from zarafe.main_window import VideoAnnotator
from zarafe.utils.theme import apply_dark_theme
from zarafe.widgets.project_dialog import ProjectDialog


def main() -> None:
    """Main application entry point."""
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    # Show project selection dialog first
    project_dialog = ProjectDialog()
    if project_dialog.exec() != ProjectDialog.DialogCode.Accepted:
        # User cancelled project selection
        sys.exit(0)

    # Get selected project info
    project_path, project_config = project_dialog.get_project_info()

    # Create and show main window with the selected project
    window = VideoAnnotator(project_path, project_config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
