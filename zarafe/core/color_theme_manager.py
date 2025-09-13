"""Color theme management for event visualization."""

from .configuration_service import ConfigurationService


class ColorThemeManager:
    """Manages color themes and caching for event visualization."""

    def __init__(self) -> None:
        """Initialize color theme manager."""
        self._color_cache: dict[str, tuple[int, int, int]] = {}
        self._config_service = ConfigurationService.get_instance()

    def get_color(self, event_name: str) -> tuple[int, int, int]:
        """Get RGB color for event type with caching."""
        if event_name in self._color_cache:
            return self._color_cache[event_name]

        config = self._config_service.get_config()
        if config is None:
            # Default color when no config loaded
            default_color = (123, 171, 61)
            self._color_cache[event_name] = default_color
            return default_color

        color = config.get_color(event_name)
        self._color_cache[event_name] = color
        return color

    def get_rgba_color(self, event_name: str, alpha: int = 255) -> tuple[int, int, int, int]:
        """Get RGBA color for event type."""
        rgb = self.get_color(event_name)
        return (*rgb, alpha)

    def get_hex_color(self, event_name: str) -> str:
        """Get hex color string for event type."""
        rgb = self.get_color(event_name)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def clear_cache(self) -> None:
        """Clear color cache when configuration changes."""
        self._color_cache.clear()

    def preload_colors(self, event_names: list[str]) -> None:
        """Preload colors for multiple event types."""
        for event_name in event_names:
            self.get_color(event_name)
