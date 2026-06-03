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
