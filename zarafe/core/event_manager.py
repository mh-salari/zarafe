"""Event creation, management, and persistence."""

import csv
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from ..utils.sorting import event_sort_key


class EventManager:
    """Manages annotation events and their persistence."""

    def __init__(self, config: ProjectConfig):
        self.events: list[dict[str, Any]] = []
        self.selected_event: int | None = None
        self.event_history: list[list[dict[str, Any]]] = []
        self.config = config
        self.event_types = config.get_event_types()

    def create_event(self, event_type: str) -> tuple[bool, str]:
        """Create new event of specified type. Returns (success, message)."""
        # Check for duplicates
        for i, event in enumerate(self.events):
            if event["name"] == event_type:
                self.selected_event = i
                return False, f"{event_type} already exists. Please complete or delete it first."

        self.save_state()
        event = {"name": event_type, "start": -1, "end": -1}
        self.events.append(event)
        self.selected_event = len(self.events) - 1

        return True, f"Created {event_type}"

    def mark_start(self, frame: int) -> tuple[bool, str]:
        """Mark start frame for selected event."""
        if self.selected_event is None:
            return False, "Please create or select an event first."

        event = self.events[self.selected_event]
        if event["end"] != -1 and frame > event["end"]:
            return False, "Start frame cannot be after end frame."

        self.save_state()
        event["start"] = frame
        return True, f"Marked start at frame {frame}"

    def mark_end(self, frame: int) -> tuple[bool, str]:
        """Mark end frame for selected event."""
        if self.selected_event is None:
            return False, "Please create or select an event first."

        event = self.events[self.selected_event]
        if event["start"] != -1 and frame < event["start"]:
            return False, "End frame cannot be before start frame."

        self.save_state()
        event["end"] = frame
        return True, f"Marked end at frame {frame}"

    def delete_selected_event(self) -> tuple[bool, str]:
        """Delete the currently selected event."""
        if self.selected_event is None:
            return False, "Please select an event to delete."

        if 0 <= self.selected_event < len(self.events):
            self.save_state()

            deleted_name = self.events[self.selected_event]["name"]
            self.events.pop(self.selected_event)

            if not self.events:
                self.selected_event = None
            elif self.selected_event >= len(self.events):
                self.selected_event = len(self.events) - 1

            return True, f"Deleted {deleted_name}"

        return False, "Invalid event selection."

    def select_event(self, index: int) -> bool:
        """Select event by index."""
        if 0 <= index < len(self.events):
            self.selected_event = index
            return True
        return False

    def jump_to_event(self, index: int, use_end: bool = False) -> int | None:
        """Get frame to jump to for event. Returns frame number or None."""
        if 0 <= index < len(self.events):
            event = self.events[index]

            if use_end and event["end"] != -1:
                return event["end"]
            elif event["start"] != -1:
                return event["start"]
            elif event["end"] != -1:
                return event["end"]

        return None

    def save_state(self) -> None:
        """Save current state for undo functionality."""
        state_copy = [event.copy() for event in self.events]
        self.event_history.append(state_copy)

        if len(self.event_history) > 20:
            self.event_history.pop(0)

    def undo(self) -> tuple[bool, str]:
        """Undo last action."""
        if not self.event_history:
            return False, "No actions to undo"

        prev_selected = self.selected_event
        self.events = self.event_history.pop()

        if prev_selected is not None and prev_selected < len(self.events):
            self.selected_event = prev_selected
        else:
            self.selected_event = None

        return True, "Undid last action"

    def get_event_display_text(self, index: int) -> str:
        """Get display text for event at index."""
        if 0 <= index < len(self.events):
            event = self.events[index]
            start_str = str(event["start"]) if event["start"] != -1 else "N/A"
            end_str = str(event["end"]) if event["end"] != -1 else "N/A"
            return f"{event['name']}: Start={start_str}, End={end_str}"
        return ""

    def save_to_csv(self, csv_path: Path, metadata_manager) -> tuple[bool, str]:
        """Save events to CSV file."""
        try:
            if not metadata_manager.is_complete():
                return False, "Please fill in all metadata fields before saving."

            annotated_monitors = set()
            rows_to_write = []

            for event in self.events:
                if self.config.is_marker_interval_event(event["name"]):
                    continue

                if event["start"] == -1 or event["end"] == -1:
                    return False, f"Event '{event['name']}' is missing start or end time."

                duration = self._calculate_duration_seconds(event, metadata_manager)
                duration_str = str(duration) if duration is not None else "N.A."

                row = [
                    metadata_manager.get_field("participant_id"),
                    metadata_manager.get_field("file_name"),
                    event["name"],
                    event["start"] if event["start"] != -1 else "N.A.",
                    event["end"] if event["end"] != -1 else "N.A.",
                    duration_str,
                ]
                rows_to_write.append(row)

            rows_to_write.sort(key=lambda x: x[3] if x[3] != "N.A." else float('inf'))

            with csv_path.open("w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "participant_id",
                    "file_name", 
                    "event_name",
                    "start_frame",
                    "end_frame",
                    "duration",
                ])
                writer.writerows(rows_to_write)

            return True, f"Events saved to {csv_path}"

        except Exception as e:
            return False, f"Failed to save events: {e!s}"

    def load_from_csv(self, csv_path: Path) -> tuple[bool, str]:
        """Load events from CSV file."""
        self.events.clear()

        try:
            with csv_path.open() as csvfile:
                reader = csv.DictReader(csvfile)
                header = reader.fieldnames

                for row in reader:
                    # Check if this is the new universal format (has event_name column)
                    if "event_name" in header:
                        event_name = row.get("event_name", "")
                        if not event_name:
                            continue
                    # Handle old muisti format (has monitor_id and event_type columns)
                    elif "monitor_id" in header and "event_type" in header:
                        event_type = row.get("event_type", "")
                        monitor_id = row.get("monitor_id", "")
                        
                        if event_type == "N.A." or not event_type or not monitor_id:
                            continue
                            
                        # Reconstruct event name from old format
                        if event_type == "approach":
                            event_name = f"Approach {monitor_id}"
                        elif event_type == "view":
                            event_name = f"View {monitor_id}"
                        else:
                            continue
                    else:
                        # Unknown format
                        continue

                    start_frame = row.get("start_frame", "N.A.")
                    end_frame = row.get("end_frame", "N.A.")

                    event = {
                        "name": event_name,
                        "start": int(start_frame) if start_frame not in ["-1", "N.A."] else -1,
                        "end": int(end_frame) if end_frame not in ["-1", "N.A."] else -1,
                    }
                    self.events.append(event)

            if self.events:
                self.selected_event = 0

            return True, f"Loaded {len(self.events)} events"

        except Exception as e:
            return False, f"Error loading events: {e}"

    def save_marker_intervals(self, video_dir: Path) -> None:
        """Save Accuracy Test events to markerInterval.tsv file."""
        marker_events = [event for event in self.events if self.config.is_marker_interval_event(event["name"])]

        if not marker_events:
            return

        marker_path = video_dir / "markerInterval.tsv"

        try:
            with marker_path.open("w", newline="") as tsvfile:
                writer = csv.writer(tsvfile, delimiter="\t")
                writer.writerow(["start_frame", "end_frame"])

                for event in marker_events:
                    if event["start"] != -1 and event["end"] != -1:
                        writer.writerow([event["start"], event["end"]])

        except Exception as e:
            print(f"Error saving marker intervals: {e}")

    def load_marker_intervals(self, marker_path: Path) -> None:
        """Load marker intervals from TSV file as marker interval events."""
        # Find the marker interval event type from config
        marker_event_name = None
        for event_type in self.config.config.get("event_types", []):
            if event_type.get("applies_to") == "glassesValidator":
                marker_event_name = event_type["name"]
                break
        
        if not marker_event_name:
            return
            
        try:
            with marker_path.open() as tsvfile:
                reader = csv.DictReader(tsvfile, delimiter="\t")

                for i, row in enumerate(reader):
                    start_frame = int(row.get("start_frame", 0))
                    end_frame = int(row.get("end_frame", 0))

                    event = {
                        "name": f"{marker_event_name} {i + 1}",
                        "start": start_frame,
                        "end": end_frame,
                    }
                    self.events.append(event)

        except Exception as e:
            print(f"Error loading marker intervals: {e}")

    def clear(self) -> None:
        """Clear all events and history."""
        self.events.clear()
        self.selected_event = None
        self.event_history.clear()

    def _calculate_duration_seconds(self, event: dict, metadata_manager) -> float | None:
        """Calculate duration in seconds for an event."""
        # This would need access to FPS - we'll need to refactor this
        # For now, return None as placeholder
        return None
