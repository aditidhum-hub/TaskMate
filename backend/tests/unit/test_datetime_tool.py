"""Unit tests for deterministic Date/Time grounding tool."""

from datetime import datetime, timezone

from backend.app.tools.datetime_tool import resolve_date_time

# Fixed anchor date: Wednesday, September 16, 2026 at 10:00:00 UTC
ANCHOR = datetime(2026, 9, 16, 10, 0, 0, tzinfo=timezone.utc)


def test_resolve_today():
    """Verify 'today' resolves to anchor date."""
    result = resolve_date_time("today", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-16"
    assert result["day_of_week"] == "Wednesday"
    assert result["human_readable"] == "Wednesday, September 16, 2026"
    assert result["relative_description"] == "Today"


def test_resolve_now_or_empty():
    """Verify empty query or 'now' defaults to anchor date."""
    result = resolve_date_time("", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-16"
    assert result["relative_description"] == "Today"

    result_now = resolve_date_time("now", anchor=ANCHOR)
    assert result_now["iso_date"] == "2026-09-16"


def test_resolve_tomorrow():
    """Verify 'tomorrow' resolves to anchor + 1 day."""
    result = resolve_date_time("tomorrow", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-17"
    assert result["day_of_week"] == "Thursday"
    assert result["relative_description"] == "Tomorrow"


def test_resolve_yesterday():
    """Verify 'yesterday' resolves to anchor - 1 day."""
    result = resolve_date_time("yesterday", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-15"
    assert result["day_of_week"] == "Tuesday"
    assert result["relative_description"] == "Yesterday"


def test_resolve_in_n_days():
    """Verify 'in N days' calculation."""
    result = resolve_date_time("in 3 days", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-19"
    assert result["day_of_week"] == "Saturday"
    assert result["relative_description"] == "In 3 days"

    result_single = resolve_date_time("in 1 day", anchor=ANCHOR)
    assert result_single["iso_date"] == "2026-09-17"
    assert result_single["relative_description"] == "In 1 day"


def test_resolve_in_n_weeks():
    """Verify 'in N weeks' calculation."""
    result = resolve_date_time("in 2 weeks", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-30"
    assert result["day_of_week"] == "Wednesday"
    assert result["relative_description"] == "In 2 weeks"


def test_resolve_in_n_hours():
    """Verify 'in N hours' calculation."""
    result = resolve_date_time("in 5 hours", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-16"
    assert result["relative_description"] == "In 5 hours"


def test_resolve_next_weekday():
    """Verify 'next <weekday>' resolves to upcoming occurrence."""
    # Anchor is Wednesday (2). Next Monday is 5 days ahead (Sept 21)
    result_mon = resolve_date_time("next monday", anchor=ANCHOR)
    assert result_mon["iso_date"] == "2026-09-21"
    assert result_mon["day_of_week"] == "Monday"
    assert result_mon["relative_description"] == "Next Monday"

    # Next Friday is 2 days ahead (Sept 18)
    result_fri = resolve_date_time("next friday", anchor=ANCHOR)
    assert result_fri["iso_date"] == "2026-09-18"
    assert result_fri["day_of_week"] == "Friday"
    assert result_fri["relative_description"] == "Next Friday"

    # Next Wednesday is exactly 7 days ahead (Sept 23)
    result_wed = resolve_date_time("next wednesday", anchor=ANCHOR)
    assert result_wed["iso_date"] == "2026-09-23"
    assert result_wed["day_of_week"] == "Wednesday"


def test_resolve_explicit_iso_date():
    """Verify parsing of explicit YYYY-MM-DD date."""
    result = resolve_date_time("2026-12-25", anchor=ANCHOR)
    assert result["iso_date"] == "2026-12-25"
    assert result["day_of_week"] == "Friday"
    assert result["human_readable"] == "Friday, December 25, 2026"


def test_resolve_unrecognized_query_fallback():
    """Verify unrecognized queries fall back safely to anchor date."""
    result = resolve_date_time("sometime next millennium", anchor=ANCHOR)
    assert result["iso_date"] == "2026-09-16"
    assert "Unrecognized date query" in result["relative_description"]


def test_resolve_realtime_system_clock():
    """Verify resolution without anchor utilizes live system clock."""
    result = resolve_date_time("today")
    assert result["iso_date"] is not None
    assert len(result["iso_date"]) == 10  # YYYY-MM-DD
    assert result["day_of_week"] in [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
