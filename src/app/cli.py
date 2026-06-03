import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from app.app import TIME_METRICS, JiraStatsExporter
from app.resources import ClosedIssuesStats
from core.cli_utils import bold, dimmed, stat_line
from core.date_ranges import DateRange
from core.utils import format_seconds

DEFAULT_ENV_PATH = Path.home() / ".secrets" / "jira-stats-exporter" / ".env"


def build_parser() -> argparse.ArgumentParser:
    """Build and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Export statistics from Atlassian Jira",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("me", help="Show current Jira user")

    issue_parser = subparsers.add_parser("issue", help="Show Jira issue data")
    issue_parser.add_argument("key", help="Jira issue key, for example ML-1234")

    closed_parser = subparsers.add_parser("closed", help="Show closed Jira issue links")
    closed_parser.add_argument(
        "--user",
        default="me",
        help="Jira responsible username or 'me'",
    )
    closed_parser.add_argument("--team", type=Path, help="File with Jira responsible usernames")
    closed_parser.add_argument("--week", type=int, help="ISO week number or negative relative week")
    closed_parser.add_argument(
        "--quarter",
        type=int,
        help="Quarter number or negative relative quarter",
    )
    closed_parser.add_argument("--month", type=int, help="Month number or negative relative month")
    closed_parser.add_argument("--day", type=int, help="Day of year or negative relative day")
    closed_parser.add_argument("--from", dest="from_date", help="Range start date in YYYY-MM-DD")
    closed_parser.add_argument("--to", dest="to_date", help="Range end date in YYYY-MM-DD")
    closed_parser.add_argument("--year", type=int, help="Year for positive week, month, or day")
    closed_parser.add_argument("--issues", action="store_true", help="Show closed issue links")

    return parser


def main() -> None:
    """Run the Jira stats exporter CLI."""
    load_dotenv(DEFAULT_ENV_PATH)
    CLIApp().run(build_parser().parse_args())


class CLIApp:
    """Run CLI commands for the Jira stats exporter."""

    def __init__(self, exporter: JiraStatsExporter | None = None) -> None:
        """Initialize class instance."""
        self._exporter = exporter or JiraStatsExporter()

    def run(self, args: argparse.Namespace) -> None:
        """Run the selected CLI command."""
        if args.command == "me":
            self._show_me()
        elif args.command == "issue":
            self._show_issue(args.key)
        elif args.command == "closed":
            self._show_closed(args)
        else:
            raise SystemExit(f"Unknown command: {args.command}")

    def _show_me(self) -> None:
        """Print current Jira user data."""
        payload = self._exporter.me()
        self._print_json(payload)

    def _show_issue(self, key: str) -> None:
        """Print Jira issue data."""
        payload = self._exporter.issue(key)
        self._print_json(payload)

    def _show_closed(self, args: argparse.Namespace) -> None:
        """Print closed issue stats."""
        try:
            date_range = DateRange.resolve(**vars(args))
        except ValueError as error:
            raise SystemExit(str(error)) from error

        users = self._get_users(args.user, args.team)
        for index, user in enumerate(users):
            if index > 0:
                print()
            stats = self._exporter.closed(user, date_range, with_summary=args.issues)
            self._print_closed_stats(stats, show_issues=args.issues)

    @staticmethod
    def _get_users(user: str, team: Path | None) -> list[str]:
        """Return Jira responsible usernames for the closed command."""
        if team is None:
            return [user]

        users = [line.strip() for line in team.read_text().splitlines() if line.strip()]
        if not users:
            raise SystemExit(f"Team file is empty: {team}")

        return users

    @staticmethod
    def _print_closed_stats(stats: ClosedIssuesStats, show_issues: bool) -> None:
        """Print closed issue statistics."""
        print(stat_line("Date Range", str(stats.date_range)))
        print(stat_line("Responsible", stats.responsible))
        print(CLIApp._closed_issues_line(stats))
        for metric_name in TIME_METRICS:
            print(
                stat_line(
                    f"Avg {metric_name}",
                    format_seconds(stats.avg_time_seconds[metric_name]),
                )
            )
        if show_issues:
            print()
            print(bold("Issues:"))
            for issue in stats.issues:
                summary = f" {dimmed(issue.summary)}" if issue.summary else ""
                print(f"  - {issue.url}{summary}")

    @staticmethod
    def _print_json(payload: object) -> None:
        """Print payload as formatted JSON."""
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    @staticmethod
    def _closed_issues_line(stats: ClosedIssuesStats) -> str:
        """Format the closed issues statistic line."""
        line = stat_line("Closed issues", str(len(stats.issues)))
        if stats.closed_issues_per_week is None:
            return line

        return f"{line} {dimmed(f'({stats.closed_issues_per_week:.1f} per week)')}"
