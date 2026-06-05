from pathlib import Path

from app.cli import DEFAULT_TEAM_MARKER, build_parser
from app.resources import ClosedIssue, ClosedIssuesStats
from core.date_ranges import DateRange


def test_parser_keeps_config_before_command() -> None:
    """Keep config path when it is specified before a command."""
    args = build_parser().parse_args(
        ["--config", "config.test.toml", "closed", "--team", "ml", "-m", "5"]
    )

    assert args.config == Path("config.test.toml")
    assert args.team == "ml"


def test_parser_reads_config_after_command() -> None:
    """Read config path when it is specified after a command."""
    args = build_parser().parse_args(
        ["closed", "--config", "config.test.toml", "--team", "-m", "5"]
    )

    assert args.config == Path("config.test.toml")
    assert args.team == DEFAULT_TEAM_MARKER


def _closed_issues_stats(issue_count: int, date_range: DateRange) -> ClosedIssuesStats:
    """Build closed issue stats for CLI tests."""
    return ClosedIssuesStats(
        responsible="krumko",
        date_range=date_range,
        issues=[
            ClosedIssue(url=f"https://jira.example.test/browse/ML-{index}", summary=None)
            for index in range(issue_count)
        ],
        avg_time_seconds={},
    )
