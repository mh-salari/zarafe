"""Project configuration management."""

import json
from pathlib import Path


class ProjectConfig:
    """Manages project-specific configuration from JSON files."""

    def __init__(self, config_path: Path) -> None:
        """Initialize project configuration from file."""
        self.config_path = config_path
        self.config = {}
        self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.config_path = config_path
        self._expand_event_types()

    def _expand_event_types(self) -> None:
        """Get list of event type names."""
        self._expanded_event_types = [event_type["name"] for event_type in self.config.get("event_types", [])]

    def get_event_types(self) -> list[str]:
        """Get expanded list of event types."""
        return self._expanded_event_types.copy()

    def get_color(self, event_name: str) -> tuple[int, int, int]:
        """Get color for event type based on event definitions."""
        default_color = self.config.get("default_color", [123, 171, 61])

        # Find exact event name match
        for event_type in self.config.get("event_types", []):
            if event_type["name"] == event_name and "color" in event_type:
                return tuple(event_type["color"])

        return tuple(default_color)

    def get_project_name(self) -> str:
        """Get project name."""
        return self.config.get("project", {}).get("name", "Video Annotation Tool")

    def is_marker_interval_event(self, event_name: str) -> bool:
        """Check if event should be saved as marker interval (glassesValidator format)."""
        for event_type in self.config.get("event_types", []):
            if event_type.get("applies_to") == "glassesValidator" and event_type["name"] == event_name:
                return True
        return False
