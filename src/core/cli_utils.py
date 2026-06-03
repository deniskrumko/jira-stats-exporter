BOLD = "\033[1m"
YELLOW = "\033[33m"
DIMMED = "\033[2m"
RESET = "\033[0m"


def stat_line(label: str, value: str) -> str:
    """Format a CLI statistic line with ANSI colors."""
    return f"{BOLD}{label}:{RESET} {YELLOW}{value}{RESET}"


def bold(value: str) -> str:
    """Format CLI text as bold."""
    return f"{BOLD}{value}{RESET}"


def dimmed(value: str) -> str:
    """Format CLI text as light gray."""
    return f"{DIMMED}{value}{RESET}"
