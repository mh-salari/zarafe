"""Zarafe - Video annotation tool for eye tracking studies."""

import sys
from PyQt6.QtWidgets import QApplication

from zarafe.main_window import VideoAnnotator
from zarafe.utils.theme import apply_dark_theme


def main() -> None:
    """Main application entry point."""
    app = QApplication(sys.argv)

    apply_dark_theme(app)

    window = VideoAnnotator()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
