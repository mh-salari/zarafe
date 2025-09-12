"""Metadata management for session data."""

import csv
from pathlib import Path

from .config import ProjectConfig


class MetadataManager:
    """Manages session metadata."""

    def __init__(self, config: ProjectConfig = None):
        self.config = config
        self.metadata = {}
        if config:
            self._initialize_fields()
        
    def set_config(self, config: ProjectConfig) -> None:
        """Set configuration and initialize metadata fields."""
        self.config = config
        self._initialize_fields()
        
    def _initialize_fields(self) -> None:
        """Initialize metadata fields from config."""
        # Get metadata schema from config or use defaults
        metadata_schema = self.config.config.get("metadata_schema", {
            "participant_id": {"type": "text", "required": True},
            "file_name": {"type": "text", "required": True},
        })
        
        # Initialize all fields as empty strings
        self.metadata = {}
        for field_name in metadata_schema.keys():
            self.metadata[field_name] = ""

    def update_field(self, field: str, value: str) -> None:
        """Update a metadata field."""
        self.metadata[field] = value

    def get_field(self, field: str) -> str:
        """Get a metadata field value."""
        return self.metadata.get(field, "")

    def is_complete(self) -> bool:
        """Check if required metadata fields are complete."""
        required_fields = ["participant_id", "condition", "series_title"]
        return all(self.metadata[field] for field in required_fields)

    def load_from_csv(self, metadata_path: Path) -> None:
        """Load metadata from CSV file."""
        try:
            with metadata_path.open() as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    # Load all fields dynamically from CSV
                    for field_name in self.metadata.keys():
                        # Try direct field name first, then check for mapping in config
                        csv_column = self._get_csv_column_name(field_name)
                        self.metadata[field_name] = row.get(csv_column, "")
                    break
        except Exception as e:
            print(f"Error loading metadata CSV: {e}")
    
    def _get_csv_column_name(self, field_name: str) -> str:
        """Get CSV column name for a metadata field, handling legacy mappings."""
        if not self.config:
            return field_name
            
        # Check if there's a CSV mapping in the config
        metadata_schema = self.config.config.get("metadata_schema", {})
        field_info = metadata_schema.get(field_name, {})
        
        # Return mapped CSV column name or default to field name
        return field_info.get("csv_column", field_name)

    def set_file_name(self, file_name: str) -> None:
        """Set the file name metadata."""
        self.metadata["file_name"] = file_name
