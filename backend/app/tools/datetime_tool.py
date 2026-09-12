"""Deterministic Date/Time grounding tool for temporal understanding."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def resolve_date_time(query: str, anchor: datetime | None = None) -> dict[str, Any]:
    """Parse relative or absolute date queries deterministically using system time.

    Args:
        query: Natural language date phrase (e.g., 'today', 'tomorrow', 'next monday',
               'in 5 days', '2026-09-15').
        anchor: Optional reference datetime. If None, uses current system time in UTC.

    Returns:
        dict[str, Any]: Standardized temporal representation with ISO string,
                        human-readable labels, and parsed offsets.
    """
    if anchor is None:
        anchor = datetime.now(timezone.utc)

    raw_query = (query or "").strip()
    normalized = raw_query.lower()

    target = anchor
    relative_desc = "Current date and time"

    if not normalized or normalized in ("today", "now", "current date", "current time"):
        target = anchor
        relative_desc = "Today"

    elif normalized == "tomorrow":
        target = anchor + timedelta(days=1)
        relative_desc = "Tomorrow"

    elif normalized == "yesterday":
        target = anchor - timedelta(days=1)
        relative_desc = "Yesterday"

    elif in_days_match := re.search(r"\bin\s+(\d+)\s+days?\b", normalized):
        days = int(in_days_match.group(1))
        target = anchor + timedelta(days=days)
        relative_desc = f"In {days} day{'s' if days != 1 else ''}"

    elif in_weeks_match := re.search(r"\bin\s+(\d+)\s+weeks?\b", normalized):
        weeks = int(in_weeks_match.group(1))
        target = anchor + timedelta(weeks=weeks)
        relative_desc = f"In {weeks} week{'s' if weeks != 1 else ''}"

    elif in_hours_match := re.search(r"\bin\s+(\d+)\s+hours?\b", normalized):
        hours = int(in_hours_match.group(1))
        target = anchor + timedelta(hours=hours)
        relative_desc = f"In {hours} hour{'s' if hours != 1 else ''}"

    elif next_day_match := re.search(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", normalized):
        day_name = next_day_match.group(1)
        target_weekday = WEEKDAYS[day_name]
        current_weekday = anchor.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = anchor + timedelta(days=days_ahead)
        relative_desc = f"Next {day_name.capitalize()}"

    elif direct_day_match := re.search(r"^(this\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", normalized):
        day_name = direct_day_match.group(2)
        target_weekday = WEEKDAYS[day_name]
        current_weekday = anchor.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = anchor + timedelta(days=days_ahead)
        relative_desc = f"{day_name.capitalize()}"

    elif re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
        try:
            parsed_date = datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            target = parsed_date
            relative_desc = f"Explicit date {normalized}"
        except ValueError:
            target = anchor
            relative_desc = f"Unrecognized date query: {raw_query}"

    else:
        # Fallback to current time if expression cannot be parsed
        target = anchor
        relative_desc = f"Unrecognized date query: {raw_query}"

    iso_date = target.strftime("%Y-%m-%d")
    iso_timestamp = target.isoformat()
    day_of_week = target.strftime("%A")
    human_readable = target.strftime("%A, %B %d, %Y")

    return {
        "query": raw_query,
        "iso_date": iso_date,
        "iso_timestamp": iso_timestamp,
        "day_of_week": day_of_week,
        "human_readable": human_readable,
        "relative_description": relative_desc,
    }
