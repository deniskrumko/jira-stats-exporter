from statistics import mean


def avg(values: list[int]) -> int:
    """Calculate an integer average for a list of values."""
    if not values:
        return 0
    return int(mean(values))


def format_seconds(seconds: int) -> str:
    """Format seconds as hours and minutes."""
    hours, remainder = divmod(seconds, 60 * 60)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"


def truncate(text: str, max_length: int, ends_with: str = "...") -> str:
    """Trim text to max length, adding a suffix when text was trimmed."""
    if max_length <= 0 or not text or len(text) <= max_length:
        return text

    if len(ends_with) >= max_length:
        return ends_with[:max_length]

    return text[: max_length - len(ends_with)] + ends_with
