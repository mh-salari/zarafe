"""Zarafe - Video annotation tool for eye tracking studies."""

import os
import sys

# Suppress Qt multimedia debug output - must be set before Qt imports
os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"

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
    project_info = project_dialog.get_project_info()
    if not project_info:
        sys.exit(0)

    project_path, project_config = project_info

    # Create and show main window with the selected project
    window = VideoAnnotator(project_path, project_config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
