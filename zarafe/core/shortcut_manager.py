"""Centralized keyboard shortcut management system."""

from collections.abc import Callable

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


class ShortcutManager:
    """Centralized manager for application keyboard shortcuts."""

    def __init__(self, parent_widget: QWidget) -> None:
        """Initialize the shortcut manager."""
        self.parent_widget = parent_widget
        self.shortcuts: dict[str, QShortcut] = {}
        self.registered = False

    def register_shortcuts(self, shortcut_map: dict[str, Callable]) -> None:
        """Register all shortcuts from a mapping of key sequence to callback."""
        if self.registered:
            return

        for key_sequence, callback in shortcut_map.items():
            self._register_single_shortcut(key_sequence, callback)

        self.registered = True

    def _register_single_shortcut(self, key_sequence: str, callback: Callable) -> None:
        """Register a single shortcut."""
        if key_sequence in self.shortcuts:
            return

        shortcut = QShortcut(QKeySequence(key_sequence), self.parent_widget)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = shortcut

    def unregister_shortcut(self, key_sequence: str) -> None:
        """Unregister a specific shortcut."""
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].deleteLater()
            del self.shortcuts[key_sequence]

    def clear_all_shortcuts(self) -> None:
        """Clear all registered shortcuts."""
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts.clear()
        self.registered = False

    def get_registered_shortcuts(self) -> dict[str, str]:
        """Get a dict of registered shortcuts and their callback names."""
        return {key: shortcut.key().toString() for key, shortcut in self.shortcuts.items()}

    def is_registered(self, key_sequence: str) -> bool:
        """Check if a shortcut is registered."""
        return key_sequence in self.shortcuts
