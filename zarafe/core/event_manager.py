"""Event creation, management, and persistence."""

import csv
import operator
from pathlib import Path
from typing import Any

from .event_type_registry import EventTypeRegistry

# History management constants
MAX_HISTORY_SIZE = 20


class EventManager:
    """Manages annotation events and their persistence."""

    def __init__(self) -> None:
        """Initialize the event manager."""
        self.events: list[dict[str, Any]] = []
        self.selected_event: int | None = None
        self.event_history: list[list[dict[str, Any]]] = []
        self.event_registry = EventTypeRegistry()
        self.event_types = self.event_registry.get_event_types()

    def create_event(self, event_type: str) -> tuple[bool, str]:
        """Create new event of specified type. Returns (success, message)."""
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

        self.save_state()

        deleted_name = self.events[self.selected_event]["name"]
        self.events.pop(self.selected_event)

        if not self.events:
            self.selected_event = None
        elif self.selected_event >= len(self.events):
            self.selected_event = len(self.events) - 1

        return True, f"Deleted {deleted_name}"

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
            if event["start"] != -1:
                return event["start"]
            if event["end"] != -1:
                return event["end"]

        return None

    def save_state(self) -> None:
        """Save current state for undo functionality."""
        state_copy = [event.copy() for event in self.events]
        self.event_history.append(state_copy)

        if len(self.event_history) > MAX_HISTORY_SIZE:
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
        event = self.events[index]
        start_str = str(event["start"]) if event["start"] != -1 else "N/A"
        end_str = str(event["end"]) if event["end"] != -1 else "N/A"
        return f"{event['name']}: Start={start_str}, End={end_str}"

    def save_to_csv(self, csv_path: Path, file_name: str) -> tuple[bool, str]:
        """Save events to CSV file."""
        try:
            rows_to_write = []

            for event in self.events:
                if event["start"] == -1 or event["end"] == -1:
                    return False, f"Event '{event['name']}' is missing start or end time."

                # Simple duration calculation in frames
                duration_frames = event["end"] - event["start"] + 1

                row = [
                    file_name,
                    event["name"],
                    event["start"],
                    event["end"],
                    duration_frames,
                ]
                rows_to_write.append(row)

            # Sort by start frame
            rows_to_write.sort(key=operator.itemgetter(2))

            with csv_path.open("w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "file_name",
                    "event_name",
                    "start_frame",
                    "end_frame",
                    "duration_frames",
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

                for row in reader:
                    event_name = row.get("event_name", "")
                    start_frame = row.get("start_frame", "N.A.")
                    end_frame = row.get("end_frame", "N.A.")

                    event = {
                        "name": event_name,
                        "start": int(start_frame) if start_frame not in {"-1", "N.A."} else -1,
                        "end": int(end_frame) if end_frame not in {"-1", "N.A."} else -1,
                    }
                    self.events.append(event)

            if self.events:
                self.selected_event = 0

            return True, f"Loaded {len(self.events)} events"

        except Exception as e:
            return False, f"Error loading events: {e}"

    def save_marker_intervals(self, video_dir: Path) -> None:
        """Save Accuracy Test events to markerInterval.tsv file."""
        marker_events = [event for event in self.events if self.event_registry.is_marker_interval_event(event["name"])]

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
        # Find the marker interval event type from registry
        marker_event_name = self.event_registry.get_marker_event_name()
        if not marker_event_name:
            return

        # Check if we already have events with this base name from CSV
        existing_names = {event["name"] for event in self.events}
        if marker_event_name in existing_names:
            # Skip loading marker intervals if we already have this event type from CSV
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
