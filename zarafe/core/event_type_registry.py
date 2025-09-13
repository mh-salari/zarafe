"""Event type registry and validation logic."""

from .configuration_service import ConfigurationService


class EventTypeRegistry:
    """Manages event type validation and metadata."""

    def __init__(self) -> None:
        """Initialize event type registry."""
        self._config_service = ConfigurationService.get_instance()

    def get_event_types(self) -> list[str]:
        """Get list of available event types."""
        config = self._config_service.get_config()
        if config is None:
            return []
        return config.get_event_types()

    def is_marker_interval_event(self, event_name: str) -> bool:
        """Check if event should be saved as marker interval."""
        config = self._config_service.get_config()
        if config is None:
            return False
        return config.is_marker_interval_event(event_name)

    def is_valid_event_type(self, event_name: str) -> bool:
        """Check if event type is valid for current project."""
        return event_name in self.get_event_types()

    def get_event_metadata(self, event_name: str) -> dict:
        """Get metadata for specific event type."""
        config = self._config_service.get_config()
        if config is None:
            return {}

        for event_type in config.config.get("event_types", []):
            if event_type["name"] == event_name:
                return event_type
        return {}

    def get_marker_event_name(self) -> str | None:
        """Get the event name that applies to glassesValidator."""
        config = self._config_service.get_config()
        if config is None:
            return None

        for event_type in config.config.get("event_types", []):
            if event_type.get("applies_to") == "glassesValidator":
                return event_type["name"]
        return None
