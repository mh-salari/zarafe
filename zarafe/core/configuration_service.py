"""Central configuration service for managing project configuration."""

from pathlib import Path
from typing import Optional

from .config import ProjectConfig


class ConfigurationService:
    """Centralized configuration management service."""

    _instance: Optional["ConfigurationService"] = None

    def __init__(self):
        """Initialize configuration service."""
        self._config: Optional[ProjectConfig] = None
        self._project_path: Optional[Path] = None

    @classmethod
    def get_instance(cls) -> "ConfigurationService":
        """Get singleton instance of configuration service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_project(self, project_path: Path, project_config: ProjectConfig) -> None:
        """Load project configuration."""
        self._project_path = project_path
        self._config = project_config

    def reload_config(self, config_path: Path) -> None:
        """Reload configuration from file."""
        if self._config is None:
            raise RuntimeError("No project loaded")
        self._config.load_config(config_path)

    def get_project_name(self) -> str:
        """Get current project name."""
        if self._config is None:
            return "Video Annotation Tool"
        return self._config.get_project_name()

    def get_project_path(self) -> Optional[Path]:
        """Get current project path."""
        return self._project_path

    def is_project_loaded(self) -> bool:
        """Check if a project is currently loaded."""
        return self._config is not None

    def get_config(self) -> Optional[ProjectConfig]:
        """Get underlying ProjectConfig instance."""
        return self._config
