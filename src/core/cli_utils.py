BOLD = "\033[1m"
YELLOW = "\033[33m"
ATTENTION = "\033[30;41m"
GOOD = "\033[30;42m"
DIMMED = "\033[2m"
RESET = "\033[0m"


def stat_line(
    label: str,
    value: str,
    label_color: str = BOLD,
    value_color: str = YELLOW,
) -> str:
    """Format a CLI statistic line with ANSI colors."""
    return f"{label_color}{label}:{RESET} {value_color}{value}{RESET}"


def bold(value: str) -> str:
    """Format CLI text as bold."""
    return f"{BOLD}{value}{RESET}"


def dimmed(value: str) -> str:
    """Format CLI text as light gray."""
    return f"{DIMMED}{value}{RESET}"
