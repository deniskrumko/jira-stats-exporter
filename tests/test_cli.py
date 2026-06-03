from datetime import date
from pathlib import Path

import pytest

from app.cli import CLIApp
from app.resources import ClosedIssue, ClosedIssuesStats
from core.date_ranges import DateRange


def test_closed_issues_line_without_weekly_rate_for_one_week() -> None:
    """Format closed issues without weekly rate for a one-week range."""
    assert (
        CLIApp._closed_issues_line(
            _closed_issues_stats(
                issue_count=12,
                date_range=DateRange(start=date(2026, 6, 1), end=date(2026, 6, 7)),
            )
        )
        == "\033[1mClosed issues:\033[0m \033[33m12\033[0m"
    )


def test_closed_issues_line_with_dimmed_weekly_rate() -> None:
    """Format closed issues with weekly rate for longer ranges."""
    assert (
        CLIApp._closed_issues_line(
            _closed_issues_stats(
                issue_count=12,
                date_range=DateRange(start=date(2026, 6, 1), end=date(2026, 6, 25)),
            )
        )
        == "\033[1mClosed issues:\033[0m \033[33m12\033[0m \033[2m(3.4 per week)\033[0m"
    )


def test_get_users_returns_user_without_team() -> None:
    """Return the selected user when team file is not provided."""
    assert CLIApp._get_users("krumko", None) == ["krumko"]


def test_get_users_reads_team_file(tmp_path: Path) -> None:
    """Read responsible users from a team file."""
    team = tmp_path / "team.txt"
    team.write_text("krumko\n\nturdubaev\n")

    assert CLIApp._get_users("me", team) == ["krumko", "turdubaev"]


def test_get_users_fails_for_empty_team_file(tmp_path: Path) -> None:
    """Fail when team file has no responsible users."""
    team = tmp_path / "team.txt"
    team.write_text("\n")

    with pytest.raises(SystemExit, match="Team file is empty"):
        CLIApp._get_users("me", team)


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
