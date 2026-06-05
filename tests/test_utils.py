from core.utils import avg, format_seconds, truncate


def test_avg_returns_integer_average() -> None:
    """Calculate an integer average."""
    assert avg([3600, 9000]) == 6300


def test_format_seconds_formats_hours_and_minutes() -> None:
    """Format seconds as hours and minutes."""
    assert format_seconds(45900) == "12h 45m"


def test_truncate_shortens_text_with_suffix() -> None:
    """Trim long text with a suffix."""
    assert truncate("A" * 20, 10) == "AAAAAAA..."
