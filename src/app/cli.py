import argparse
import json
from pathlib import Path

from rich import print
from rich.panel import Panel

from app.app import App
from app.config import AppConfig, CLIConfig
from app.resources import IssueGroup
from core.cli_utils import print_stat
from core.date_ranges import DateRange
from core.utils import format_seconds, truncate

DEFAULT_TEAM_MARKER = "__default__"


def add_config_argument(parser: argparse.ArgumentParser, default: Path | str | None = None) -> None:
    """Add the shared config path option to an argument parser."""
    parser.add_argument(
        "--config",
        default=default,
        type=Path,
        help="Path to the Jira stats exporter TOML config",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Export statistics from Atlassian Jira",
    )
    add_config_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_config_argument(
        subparsers.add_parser("me", help="Show current Jira user"),
        argparse.SUPPRESS,
    )

    issue_parser = subparsers.add_parser(
        "issue",
        help="Show Jira issue data",
    )
    add_config_argument(issue_parser, argparse.SUPPRESS)
    issue_parser.add_argument(
        "key",
        help="Jira issue key, for example ML-1234",
    )

    closed_parser = subparsers.add_parser(
        "closed",
        help="Show closed Jira issue links",
    )
    add_config_argument(closed_parser, argparse.SUPPRESS)
    closed_parser.add_argument(
        "-u",
        "--user",
        default="me",
        help="Jira responsible username or 'me'",
    )
    closed_parser.add_argument(
        "-t",
        "--team",
        nargs="?",
        const=DEFAULT_TEAM_MARKER,
        help="Use configured team users, optionally by shortcut",
    )
    closed_parser.add_argument(
        "-w",
        "--week",
        type=int,
        help="ISO week number or negative relative week",
    )
    closed_parser.add_argument(
        "-q",
        "--quarter",
        type=int,
        help="Quarter number or negative relative quarter",
    )
    closed_parser.add_argument(
        "-m",
        "--month",
        type=int,
        help="Month number or negative relative month",
    )
    closed_parser.add_argument(
        "-d",
        "--day",
        type=int,
        help="Day of year or negative relative day",
    )
    closed_parser.add_argument(
        "--from",
        dest="from_date",
        help="Range start date in YYYY-MM-DD",
    )
    closed_parser.add_argument(
        "--to",
        dest="to_date",
        help="Range end date in YYYY-MM-DD",
    )
    closed_parser.add_argument(
        "-y",
        "--year",
        type=int,
        help="Year for positive week, month, or day",
    )
    closed_parser.add_argument(
        "-i",
        "--issues",
        action="store_true",
        help="Show closed issue links",
    )

    return parser


def main() -> None:
    """Run the Jira stats exporter CLI."""
    try:
        CLIApp().run(build_parser().parse_args())
    except KeyboardInterrupt:
        print("\nGoodbye!")


class CLIApp:
    """Run CLI commands for the Jira stats exporter."""

    def __init__(self, exporter: App | None = None) -> None:
        """Initialize class instance."""
        self._app = exporter
        self._cli_config = CLIConfig()

    def run(self, args: argparse.Namespace) -> None:
        """Run the selected CLI command."""
        self._init_app(args)

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
        payload = self.app.me()
        self._print_json(payload)

    def _show_issue(self, key: str) -> None:
        """Print Jira issue data."""
        payload = self.app.issue(key)
        self._print_json(payload)

    def _show_closed(self, args: argparse.Namespace) -> None:
        """Print closed issue stats."""
        try:
            date_range = DateRange.resolve(**vars(args))
        except ValueError as error:
            raise SystemExit(str(error)) from error

        users = [args.user]
        team = None
        if args.team is not None:
            team_name = None if args.team == DEFAULT_TEAM_MARKER else args.team
            try:
                team = self.app.get_team(team_name)
                users = team.users
            except (FileNotFoundError, ValueError) as error:
                raise SystemExit(str(error)) from error

        if team:
            print(Panel.fit(f"[bold green]Team: {team}[/]", border_style="green"), end="\n\n")

        for index, user in enumerate(users):
            if index > 0:
                print()

            issue_group = self.app.get_closed_issues(
                user,
                date_range,
                with_summary=args.issues,
            )
            self._print_issue_group(issue_group, show_details=args.issues)

    def _init_app(self, args: argparse.Namespace) -> None:
        """Initialize Jira stats exporter."""
        if self._app is not None:
            return

        try:
            config = AppConfig.load(args.config)
            self._cli_config = config.cli
            self._app = App(config=config)
        except Exception as e:
            print(f"[red]Failed to init app:\n{e}[/]")
            exit(1)

    @property
    def app(self) -> App:
        """Return initialized Jira stats exporter."""
        if self._app is None:
            raise RuntimeError("Jira stats exporter is not initialized")
        return self._app

    def _print_issue_group(self, issue_group: IssueGroup, show_details: bool = True) -> None:
        """Print closed issue statistics."""
        print_stat("Date Range", issue_group.date_range.colored_string, value_color=None)
        print_stat("User", issue_group.responsible)
        self._print_issues_number(issue_group)

        for metric_name, avg_time in issue_group.avg_time_in_status.items():
            print_stat(f"Avg {metric_name}", format_seconds(avg_time))

        if show_details:
            print("\n[bold]Issues:[/]")
            for issue in issue_group.issues:
                summary = truncate(issue.summary or "", self._cli_config.max_summary_length)
                print(f"[cyan bold link={issue.url}]{issue.code}[/]: {summary}")

    @staticmethod
    def _print_json(payload: object) -> None:
        """Print payload as formatted JSON."""
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    @staticmethod
    def _print_issues_number(issue_group: IssueGroup, display_name: str = "Issues") -> None:
        """Format the closed issues statistic line."""
        value_color = "yellow not b"

        # No tasks closed in 3 days - bad
        if issue_group.count == 0 and issue_group.date_range.days >= 3:
            value_color = "red"

        # More than 3 tasks per week - good
        elif issue_group.count > 3 and issue_group.date_range.days <= 7:
            value_color = "green"

        line = str(issue_group.count)
        if issue_group.issues_per_week:
            line += f" [dim]({issue_group.issues_per_week:.1f}/week)[/dim]"

        print_stat(display_name, line, value_color=value_color)
