"""Menu bar management for the main application window."""

from PyQt6.QtWidgets import QMenuBar


class MenuManager:
    """Manages application menu bar setup and state."""

    def __init__(self) -> None:
        """Initialize the menu manager."""
        self.edit_project_action = None

    def setup_menu_bar(
        self, menu_bar: QMenuBar, open_callback: object, edit_callback: object, about_callback: object
    ) -> None:
        """Setup complete application menu bar with callbacks."""
        self._create_project_menu(menu_bar, open_callback, edit_callback)
        self._create_help_menu(menu_bar, about_callback)

    def _create_project_menu(self, menu_bar: QMenuBar, open_callback: object, edit_callback: object) -> None:
        """Create project management menu."""
        project_menu = menu_bar.addMenu("&Project")

        # Open/Select Project
        open_project_action = project_menu.addAction("&Open Project...")
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(open_callback)

        project_menu.addSeparator()

        # Edit Current Project (initially disabled)
        self.edit_project_action = project_menu.addAction("&Edit Current Project...")
        self.edit_project_action.setShortcut("Ctrl+E")
        self.edit_project_action.setEnabled(False)
        self.edit_project_action.triggered.connect(edit_callback)

    @staticmethod
    def _create_help_menu(menu_bar: QMenuBar, about_callback: object) -> None:
        """Create help menu."""
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(about_callback)

    def enable_project_editing(self) -> None:
        """Enable edit project menu item when project is loaded."""
        if self.edit_project_action:
            self.edit_project_action.setEnabled(True)

    def disable_project_editing(self) -> None:
        """Disable edit project menu item."""
        if self.edit_project_action:
            self.edit_project_action.setEnabled(False)
