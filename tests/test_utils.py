from core.utils import avg, format_seconds


def test_avg_returns_integer_average() -> None:
    """Calculate an integer average."""
    assert avg([3600, 9000]) == 6300


def test_avg_returns_zero_for_empty_values() -> None:
    """Return zero for empty values."""
    assert avg([]) == 0


def test_format_seconds_formats_hours_and_minutes() -> None:
    """Format seconds as hours and minutes."""
    assert format_seconds(45900) == "12h 45m"
