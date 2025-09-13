"""Icon loading utilities for SVG icons."""

from pathlib import Path

from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

from zarafe.utils.file_utils import get_resource_path


class IconLoader:
    """Utility class for loading and managing SVG icons."""

    def __init__(self, icon_directory: Path) -> None:
        """Initialize icon loader with icon directory path."""
        self.icon_directory = icon_directory
        self._cache = {}

    def get_icon(self, icon_name: str, size: int = 24, color: str | None = None) -> QIcon:
        """Load an SVG icon and return as QIcon.

        Args:
            icon_name: Name of the icon file (without .svg extension)
            size: Size in pixels for the icon
            color: Optional color override (hex format like '#ffffff')

        Returns:
            QIcon object ready for use in Qt widgets

        """
        cache_key = f"{icon_name}_{size}_{color}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        icon_path = self.icon_directory / f"{icon_name}.svg"

        # Create SVG renderer - we know our icons exist
        renderer = QSvgRenderer(str(icon_path))

        # Create pixmap with the specified size
        pixmap = QPixmap(size, size)
        pixmap.fill(QApplication.palette().color(QApplication.palette().ColorRole.Window))

        # Render SVG to pixmap using QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        # Create and cache icon
        icon = QIcon(pixmap)
        self._cache[cache_key] = icon

        return icon

    def get_pixmap(self, icon_name: str, size: int = 24) -> QPixmap:
        """Load an SVG icon and return as QPixmap.

        Args:
            icon_name: Name of the icon file (without .svg extension)
            size: Size in pixels for the icon

        Returns:
            QPixmap object

        """
        icon_path = self.icon_directory / f"{icon_name}.svg"

        # Create SVG renderer - we know our icons exist
        renderer = QSvgRenderer(str(icon_path))

        pixmap = QPixmap(size, size)
        pixmap.fill(QApplication.palette().color(QApplication.palette().ColorRole.Window))

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap


# Create the icon loader once at module level
_icon_loader = IconLoader(get_resource_path("icons"))


def load_icon(icon_name: str, size: int = 24, color: str | None = None) -> QIcon:
    """Load an icon using the module-level icon loader."""
    return _icon_loader.get_icon(icon_name, size, color)
