from core.utils import avg, format_seconds, truncate


def test_avg_returns_integer_average() -> None:
    """Calculate an integer average."""
    assert avg([3600, 9000]) == 6300


def test_avg_returns_zero_for_empty_values() -> None:
    """Return zero for empty values."""
    assert avg([]) == 0


def test_format_seconds_formats_hours_and_minutes() -> None:
    """Format seconds as hours and minutes."""
    assert format_seconds(45900) == "12h 45m"


def test_truncate_shortens_text_with_suffix() -> None:
    """Trim long text with a suffix."""
    assert truncate("A" * 20, 10) == "AAAAAAA..."


def test_truncate_shortens_suffix_when_suffix_is_too_long() -> None:
    """Trim suffix when it is longer than max length."""
    assert truncate("A" * 20, 2) == ".."


def test_truncate_does_not_shorten_text_when_limit_is_not_positive() -> None:
    """Return original text when max length is not positive."""
    assert truncate("A" * 20, 0) == "A" * 20
    assert truncate("A" * 20, -1) == "A" * 20
