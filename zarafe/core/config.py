"""Project configuration management."""

import json
from pathlib import Path


class ProjectConfig:
    """Manages project-specific configuration from JSON files."""

    def __init__(self, config_path: Path):
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
        """Expand event type templates with target IDs."""
        expanded_types = []
        
        for event_type in self.config.get("event_types", []):
            if event_type.get("applies_to") == "targets":
                # Expand template for each target
                for target in self.config.get("targets", []):
                    expanded_name = event_type["name"].replace("{target}", target["id"])
                    expanded_types.append(expanded_name)
            else:
                # Single event type (glassesValidator, global, etc.)
                expanded_types.append(event_type["name"])
        
        self._expanded_event_types = expanded_types

    def get_event_types(self) -> list[str]:
        """Get expanded list of event types."""
        return self._expanded_event_types.copy()

    def get_conditions(self) -> list[str]:
        """Get list of condition options."""
        return self.config.get("conditions", []).copy()

    def get_targets(self) -> list[dict[str, str]]:
        """Get list of targets/monitors."""
        return self.config.get("targets", []).copy()

    def get_color(self, event_name: str) -> tuple[int, int, int]:
        """Get color for event type based on event definitions."""
        default_color = self.config.get("default_color", [123, 171, 61])
        
        # Check event types for direct color assignments
        for event_type in self.config.get("event_types", []):
            if "color" in event_type:
                # For template events, match the expanded name pattern
                if event_type.get("applies_to") == "targets" and "{target}" in event_type["name"]:
                    template_base = event_type["name"].replace(" {target}", "")
                    if event_name.startswith(template_base):
                        return tuple(event_type["color"])
                # For direct name match
                elif event_type["name"] in event_name:
                    return tuple(event_type["color"])
        
        return tuple(default_color)

    def get_project_name(self) -> str:
        """Get project name."""
        return self.config.get("project", {}).get("name", "Video Annotation Tool")

    def get_target_ids(self) -> list[str]:
        """Get list of target IDs for metadata fields."""
        return [target["id"] for target in self.config.get("targets", [])]

    def is_marker_interval_event(self, event_name: str) -> bool:
        """Check if event should be saved as marker interval (glassesValidator format)."""
        for event_type in self.config.get("event_types", []):
            if event_type.get("applies_to") == "glassesValidator" and event_type["name"] in event_name:
                return True
        return False