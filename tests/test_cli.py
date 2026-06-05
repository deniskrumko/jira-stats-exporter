from datetime import date
from pathlib import Path

from app.cli import DEFAULT_TEAM_MARKER, CLIApp, build_parser
from app.config import CLIConfig
from app.resources import Issue, Issues, IssueStatus
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


def test_print_issues_truncates_summary(capsys) -> None:
    """Trim issue summaries using configured CLI summary length."""
    app = CLIApp()
    app._cli_config = CLIConfig(max_summary_length=10)
    issues = Issues(
        responsible="krumko",
        date_range=DateRange(start=date(2026, 5, 1), end=date(2026, 5, 7)),
        issues=[
            Issue(
                url="https://jira.example.test/browse/ML-1",
                summary="A" * 120,
                status=IssueStatus.CLOSED,
            )
        ],
        avg_time_in_status={"TTM": 0},
    )

    app._print_issues(issues)

    output = capsys.readouterr().out
    assert "AAAAAAA..." in output


def _closed_issues_stats(issue_count: int, date_range: DateRange) -> Issues:
    """Build closed issue stats for CLI tests."""
    return Issues(
        responsible="krumko",
        date_range=date_range,
        issues=[
            Issue(
                url=f"https://jira.example.test/browse/ML-{index}",
                summary=None,
                status=IssueStatus.CLOSED,
            )
            for index in range(issue_count)
        ],
        avg_time_in_status={},
    )
