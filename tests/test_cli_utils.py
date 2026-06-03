from core.cli_utils import bold, dimmed, stat_line


def test_stat_line_colors_label_and_value() -> None:
    """Format a colored CLI statistic line."""
    assert stat_line("Responsible", "krumko") == "\033[1mResponsible:\033[0m \033[33mkrumko\033[0m"


def test_dimmed_colors_text() -> None:
    """Format text as dimmed."""
    assert dimmed("summary") == "\033[2msummary\033[0m"


def test_bold_colors_text() -> None:
    """Format text as bold."""
    assert bold("Issues:") == "\033[1mIssues:\033[0m"
