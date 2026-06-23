from rich import print


def print_stat(
    label: str,
    value: object,
    label_color: str | None = "bold",
    value_color: str | None = "yellow",
) -> None:
    """Print a CLI statistic line with ANSI colors using rich."""
    if label_color:
        label = f"[{label_color}]{label}[/{label_color}]"

    if value_color:
        value = f"[{value_color}]{value}[/{value_color}]"

    print(f"{label}: {value}")
