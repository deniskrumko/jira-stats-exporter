import argparse
import json
import traceback

from rich import print
from rich.markup import escape
from rich.panel import Panel

from app.app import App
from app.config import AppConfig, CLIConfig
from app.resources import Issue, IssueGroup
from core.cli_utils import print_stat
from core.date_ranges import DateRange
from core.utils import format_seconds, truncate
from teams import Team

from .parser import build_parser
from .resources import DEFAULT_TEAM_MARKER, CLICommands


def main() -> None:
    """Run the Jira stats exporter CLI."""
    try:
        CLIApp().run(build_parser().parse_args())
    except KeyboardInterrupt:
        print("\n[red]Goodbye![/]")


class CLIApp:
    """Run CLI commands for the Jira stats exporter."""

    def __init__(self, exporter: App | None = None) -> None:
        """Initialize class instance."""
        self._app = exporter
        self._cli_config = CLIConfig()

    @property
    def app(self) -> App:
        """Return initialized Jira stats exporter."""
        if self._app is None:
            raise RuntimeError("Jira stats exporter is not initialized")
        return self._app

    def run(self, args: argparse.Namespace) -> None:
        """Run the selected CLI command."""
        self._init_app(args)

        if args.command == CLICommands.ME:
            self._show_me()
        elif args.command == CLICommands.ISSUE:
            self._show_issue(args.key, raw=args.raw)
        elif args.command == CLICommands.CLOSED:
            self._show_closed(args)
        elif args.command == CLICommands.IN_PROGRESS:
            self._show_in_progress(args)
        else:
            raise SystemExit(f"Unknown command: {args.command}")

    def _init_app(self, args: argparse.Namespace) -> None:
        """Initialize Jira stats exporter."""
        if self._app is not None:
            return

        try:
            config = AppConfig.load(args.config)
            self._cli_config = config.cli
            self._app = App.from_config(config)
        except Exception as e:
            print(f"[red]Failed to init app:\n{e!r}[/]")
            traceback.print_exception(e)
            exit(1)

    # COMMANDS

    def _show_me(self) -> None:
        """Show current Jira user data."""
        payload = self.app.me()
        self._print_json(payload)

    def _show_issue(self, key: str, raw: bool = False) -> None:
        """Show Jira issue data."""
        issue = self.app.issue(key)
        if raw:
            self._print_json(issue.raw)
            return

        self._print_issue(issue)

    def _show_closed(self, args: argparse.Namespace) -> None:
        """Show closed issues."""
        try:
            date_range = DateRange.resolve(**vars(args))
        except ValueError as error:
            raise SystemExit(str(error)) from error

        users, team = self._get_users_and_team(args)
        total_tasks, total_ttm = 0, 0
        for index, user in enumerate(users):
            if index > 0:
                print()

            issue_group = self.app.get_closed_issues(
                user,
                date_range,
                with_summary=args.issues,
            )
            self._print_issue_group(issue_group, show_details=args.issues)
            total_tasks += issue_group.count
            total_ttm += issue_group.total_ttm

        if team:
            avg_ttm = format_seconds(total_ttm // total_tasks)
            print(f"\n[bold green]Total tasks: {total_tasks}\nAverage TTM: {avg_ttm}[/]")

    def _show_in_progress(self, args: argparse.Namespace) -> None:
        """Show in-progress issues."""
        users, _ = self._get_users_and_team(args)

        for index, user in enumerate(users):
            if index > 0:
                print()

            issue_group = self.app.get_in_progress_issues(user)
            self._print_issue_group(
                issue_group,
                show_issues_number=False,
                show_metrics=False,
            )

    # HELPERS

    def _get_users_and_team(
        self,
        args: argparse.Namespace,
        display_team: bool = True,
    ) -> tuple[list[str], Team | None]:
        users: list[str] = [args.user]
        team = None

        if args.team is not None:
            team_name = None if args.team == DEFAULT_TEAM_MARKER else args.team
            try:
                team = self.app.get_team(team_name)
                users = team.users
            except (FileNotFoundError, ValueError) as error:
                raise SystemExit(str(error)) from error

        if team and display_team:
            print(Panel.fit(f"[bold green]Team: {team}[/]", border_style="green"), end="\n\n")

        return users, team

    def _print_issue_group(
        self,
        issue_group: IssueGroup,
        show_date_range: bool = True,
        show_user: bool = True,
        show_issues_number: bool = True,
        show_metrics: bool = True,
        show_details: bool = True,
    ) -> None:
        """Print closed issue statistics."""
        if show_date_range and issue_group.date_range:
            print_stat("Date Range", issue_group.date_range.colored_string, value_color=None)

        if show_user and issue_group.user:
            print_stat("User", issue_group.user)

        if show_issues_number:
            self._print_issues_number(issue_group)

        if show_metrics:
            for metric_name, avg_time in (issue_group.avg_time_in_status or {}).items():
                print_stat(f"Avg {metric_name}", format_seconds(avg_time))

        if show_details:
            prefix = "\n" if show_metrics else ""
            suffix = " [red]no issues[/]" if not issue_group.issues else ""
            print(f"{prefix}[bold]Issues:[/]{suffix}")
            for issue in issue_group.issues:
                summary = truncate(issue.summary or "", self._cli_config.max_summary_length)
                print(f"[cyan bold link={issue.url}]{issue.code}[/]: {summary}")

    @staticmethod
    def _print_json(payload: object) -> None:
        """Print payload as formatted JSON."""
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    @staticmethod
    def _print_issue(issue: Issue) -> None:
        """Print Jira issue details."""
        print_stat("Title", escape(issue.title or ""))
        print_stat("Assignee", escape(issue.assignee or ""))
        print_stat("Status", escape(issue.status or ""))
        print_stat("Labels", ", ".join(issue.labels))
        print_stat("URL", escape(issue.url or ""))
        print_stat("Description", escape(issue.description or ""))

    @staticmethod
    def _print_issues_number(issue_group: IssueGroup, display_name: str = "Issues") -> None:
        """Format the closed issues statistic line."""
        value_color = "yellow not b"

        # No tasks closed in 3 days - bad
        if issue_group.count == 0 and issue_group.date_range and issue_group.date_range.days >= 3:
            value_color = "red"

        # More than 3 tasks per week - good
        elif issue_group.count > 3 and issue_group.date_range and issue_group.date_range.days <= 7:
            value_color = "green"

        line = str(issue_group.count)
        if issue_group.date_range and issue_group.issues_per_week:
            line += f" [dim]({issue_group.issues_per_week:.1f}/week)[/dim]"

        print_stat(display_name, line, value_color=value_color)
