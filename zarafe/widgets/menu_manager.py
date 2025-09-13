"""Menu bar management for the main application window."""

from PyQt6.QtWidgets import QMenuBar


class MenuManager:
    """Manages application menu bar setup and state."""

    def __init__(self) -> None:
        """Initialize the menu manager."""
        self.edit_project_action = None
        self.import_videos_action = None

    def setup_menu_bar(
        self,
        menu_bar: QMenuBar,
        open_callback: object,
        edit_callback: object,
        import_callback: object,
        about_callback: object,
    ) -> None:
        """Setup complete application menu bar with callbacks."""
        self._create_project_menu(menu_bar, open_callback, edit_callback, import_callback)
        self._create_about_menu(menu_bar, about_callback)

    def _create_project_menu(
        self, menu_bar: QMenuBar, open_callback: object, edit_callback: object, import_callback: object
    ) -> None:
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

        # Import Videos (initially disabled)
        self.import_videos_action = project_menu.addAction("&Import Videos...")
        self.import_videos_action.setShortcut("Ctrl+I")
        self.import_videos_action.setEnabled(False)
        self.import_videos_action.triggered.connect(import_callback)

    @staticmethod
    def _create_about_menu(menu_bar: QMenuBar, about_callback: object) -> None:
        """Create about menu."""
        about_menu = menu_bar.addMenu("&About")
        about_action = about_menu.addAction("&About Zarafe")
        about_action.triggered.connect(about_callback)

    def enable_project_editing(self) -> None:
        """Enable edit project menu item when project is loaded."""
        if self.edit_project_action:
            self.edit_project_action.setEnabled(True)

    def disable_project_editing(self) -> None:
        """Disable edit project menu item."""
        if self.edit_project_action:
            self.edit_project_action.setEnabled(False)

    def enable_import_videos(self) -> None:
        """Enable import videos menu item when project is loaded."""
        if self.import_videos_action:
            self.import_videos_action.setEnabled(True)

    def disable_import_videos(self) -> None:
        """Disable import videos menu item."""
        if self.import_videos_action:
            self.import_videos_action.setEnabled(False)
