from datetime import date
from typing import Any

import pytest

from core import date_ranges
from core.date_ranges import DateRange


class FrozenDate(date):
    """Return a stable current date for date range tests."""

    @classmethod
    def today(cls) -> date:
        """Return a fixed Wednesday date."""
        return cls(2026, 6, 3)


@pytest.fixture(autouse=True)
def freeze_today(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze date_ranges.date.today for deterministic tests."""
    monkeypatch.setattr(date_ranges, "date", FrozenDate)


def test_positive_month_uses_current_year_by_default() -> None:
    """Resolve a positive month using the current year by default."""
    assert DateRange.resolve(month=5) == DateRange(
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )


def test_positive_month_uses_explicit_year() -> None:
    """Resolve a positive month using an explicit year."""
    assert DateRange.resolve(month=2, year=2024) == DateRange(
        start=date(2024, 2, 1),
        end=date(2024, 2, 29),
    )


def test_positive_quarter_uses_current_year_by_default() -> None:
    """Resolve a positive quarter using the current year by default."""
    assert DateRange.resolve(quarter=2) == DateRange(
        start=date(2026, 4, 1),
        end=date(2026, 6, 30),
    )


def test_positive_quarter_uses_explicit_year() -> None:
    """Resolve a positive quarter using an explicit year."""
    assert DateRange.resolve(quarter=1, year=2025) == DateRange(
        start=date(2025, 1, 1),
        end=date(2025, 3, 31),
    )


def test_positive_week_uses_iso_week() -> None:
    """Resolve a positive ISO week from Monday to Sunday."""
    assert DateRange.resolve(week=1, year=2026) == DateRange(
        start=date(2025, 12, 29),
        end=date(2026, 1, 4),
    )


def test_negative_week_uses_previous_full_week_and_ignores_year() -> None:
    """Resolve a negative week as the previous full Monday to Sunday week."""
    assert DateRange.resolve(week=-1, year=1999) == DateRange(
        start=date(2026, 5, 25),
        end=date(2026, 5, 31),
    )


def test_zero_week_uses_current_full_week_and_ignores_year() -> None:
    """Resolve zero week as the current week up to today."""
    assert DateRange.resolve(week=0, year=1999) == DateRange(
        start=date(2026, 6, 1),
        end=date(2026, 6, 3),
    )


def test_negative_month_uses_relative_month_and_ignores_year() -> None:
    """Resolve a negative month relative to today while ignoring year."""
    assert DateRange.resolve(month=-1, year=1999) == DateRange(
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )


def test_zero_month_uses_current_month_and_ignores_year() -> None:
    """Resolve zero month as the current month up to today."""
    assert DateRange.resolve(month=0, year=1999) == DateRange(
        start=date(2026, 6, 1),
        end=date(2026, 6, 3),
    )


def test_negative_quarter_uses_relative_quarter_and_ignores_year() -> None:
    """Resolve a negative quarter relative to today while ignoring year."""
    assert DateRange.resolve(quarter=-1, year=1999) == DateRange(
        start=date(2026, 1, 1),
        end=date(2026, 3, 31),
    )


def test_zero_quarter_uses_current_quarter_and_ignores_year() -> None:
    """Resolve zero quarter as the current quarter up to today."""
    assert DateRange.resolve(quarter=0, year=1999) == DateRange(
        start=date(2026, 4, 1),
        end=date(2026, 6, 3),
    )


def test_negative_day_uses_relative_day_and_ignores_year() -> None:
    """Resolve a negative day relative to today while ignoring year."""
    assert DateRange.resolve(day=-1, year=1999) == DateRange(
        start=date(2026, 6, 2),
        end=date(2026, 6, 2),
    )


def test_zero_day_uses_current_day_and_ignores_year() -> None:
    """Resolve zero day as the current day."""
    assert DateRange.resolve(day=0, year=1999) == DateRange(
        start=date(2026, 6, 3),
        end=date(2026, 6, 3),
    )


def test_positive_day_uses_day_of_year() -> None:
    """Resolve a positive day as a day of year."""
    assert DateRange.resolve(day=60, year=2024) == DateRange(
        start=date(2024, 2, 29),
        end=date(2024, 2, 29),
    )


def test_explicit_range_requires_both_dates() -> None:
    """Reject an explicit date range with only one bound."""
    with pytest.raises(ValueError, match="--from and --to"):
        DateRange.resolve(from_date="2026-05-01")


def test_explicit_range_uses_given_dates() -> None:
    """Resolve an explicit inclusive date range."""
    assert DateRange.resolve(from_date="2026-05-01", to_date="2026-05-31") == DateRange(
        start=date(2026, 5, 1),
        end=date(2026, 5, 31),
    )


def test_date_range_formats_as_string() -> None:
    """Format a date range as a string."""
    assert str(DateRange(start=date(2026, 1, 1), end=date(2026, 3, 31))) == (
        "2026-01-01 – 2026-03-31"
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"quarter": 5}, "--quarter must be between 1 and 4"),
        ({"month": 13}, "--month must be between 1 and 12"),
        ({"day": 367, "year": 2026}, "Invalid day for year 2026"),
        ({"from_date": "2026-06-01", "to_date": "2026-05-31"}, "--from cannot be later"),
    ],
)
def test_invalid_date_ranges(kwargs: dict[str, Any], message: str) -> None:
    """Reject invalid date range options."""
    with pytest.raises(ValueError, match=message):
        DateRange.resolve(**kwargs)


def test_rejects_multiple_range_options() -> None:
    """Reject multiple date range option groups."""
    with pytest.raises(ValueError, match="Specify exactly one date range option"):
        DateRange.resolve(month=5, day=1)
