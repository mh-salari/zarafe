"""Metadata management for session data."""

import csv
from pathlib import Path


class MetadataManager:
    """Manages session metadata."""

    def __init__(self):
        self.metadata = {
            "participant_id": "",
            "condition": "",
            "series_title": "",
            "file_name": "",
            "M1": "",
            "M2": "",
            "M3": "",
            "M4": "",
        }

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
                    self.metadata["participant_id"] = row.get("participant_id", "")
                    self.metadata["condition"] = row.get("condition", "")
                    self.metadata["series_title"] = row.get("series_title", "")
                    self.metadata["M1"] = row.get("monitor_1_image", "")
                    self.metadata["M2"] = row.get("monitor_2_image", "")
                    self.metadata["M3"] = row.get("monitor_3_image", "")
                    self.metadata["M4"] = row.get("monitor_4_image", "")
                    break
        except Exception as e:
            print(f"Error loading metadata CSV: {e}")

    def set_file_name(self, file_name: str) -> None:
        """Set the file name metadata."""
        self.metadata["file_name"] = file_name
