"""About dialog for application information."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

from ..utils.file_utils import get_resource_path

# Dialog constants
DIALOG_MIN_WIDTH = 500
IMAGE_SCALE_WIDTH = 400
IMAGE_SCALE_HEIGHT = 100


class AboutDialog(QDialog):
    """Application about dialog."""

    def __init__(self, parent: object = None) -> None:
        """Initialize the about dialog."""
        super().__init__(parent)
        self.setWindowTitle("About Zarafe")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)

        layout = QVBoxLayout()

        # Title section
        title_label = QLabel("<h2>Zarafe - Video Annotation Tool</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description and acknowledgments
        desc_text = QLabel(
            "<p>Developed by Mohammadhossein Salari with the assistance of Claude 3.7 Sonnet.</p>"
            "<p>Video annotation tool for marking timed events in eye tracking research.</p>"
            "<p>For more information and source code, please visit:<br>"
            "<a href='https://github.com/mh-salari/zarafe'>https://github.com/mh-salari/zarafe</a></p>"
            "<h3>Acknowledgments</h3>"
            "<p>This project has received funding from the European Union's Horizon "
            "Europe research and innovation funding program under grant "
            "agreement No 101072410, Eyes4ICU project.</p>"
        )
        desc_text.setOpenExternalLinks(True)
        desc_text.setWordWrap(True)
        desc_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_text)

        # Funding acknowledgment image
        image_label = QLabel()
        image_path = get_resource_path("Funded_by_EU_Eyes4ICU.png")
        pixmap = QPixmap(str(image_path))
        image_label.setPixmap(
            pixmap.scaled(
                IMAGE_SCALE_WIDTH,
                IMAGE_SCALE_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        self.setLayout(layout)
