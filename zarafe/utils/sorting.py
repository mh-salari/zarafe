"""Sorting utilities for natural ordering."""

import re


def natural_sort_key(s: str) -> list[int | str]:
    """Generate sort key for natural ordering of strings with numbers."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def event_sort_key(row: str) -> float:
    """Generate sort key for event rows, handling N.A. values."""
    start_value = row[2]  # start_frame column
    if start_value == "N.A.":
        return float("inf")
    try:
        return int(start_value)
    except (ValueError, TypeError):
        return float("inf")
