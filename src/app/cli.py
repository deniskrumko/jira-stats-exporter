import argparse
import subprocess
import traceback
import webbrowser
from collections.abc import Callable

from rich import print

from app.app import App
from app.config import AppConfig, CLIConfig
from app.printer import CLIPrinter
from app.resources import IssueGroup
from core.date_ranges import DateRange
from reporter import ABCReporterClient, HTMLReporter
from teams import Team

from .parser import build_parser
from .resources import DEFAULT_TEAM_MARKER, CLICommands

type IssueGroupLoader = Callable[[str], IssueGroup]
type IssueGroupRenderer = Callable[[IssueGroup], None]


def main() -> None:
    """Run the Jira stats exporter CLI."""
    try:
        CLIApp().run(build_parser().parse_args())
    except KeyboardInterrupt:
        print("\n[red]Goodbye![/]")


class CLIApp:
    """Run CLI commands for the Jira stats exporter."""

    def __init__(
        self,
        exporter: App | None = None,
        reporter: ABCReporterClient | None = None,
    ) -> None:
        """Initialize class instance."""
        self._app = exporter
        self._reporter = reporter
        self._printer = CLIPrinter(CLIConfig())

    @property
    def app(self) -> App:
        """Return initialized Jira stats exporter."""
        if self._app is None:
            raise RuntimeError("Jira stats exporter is not initialized")
        return self._app

    @property
    def reporter(self) -> ABCReporterClient:
        """Return initialized report client."""
        if self._reporter is None:
            raise RuntimeError("Reporter client is not initialized")
        return self._reporter

    def run(self, args: argparse.Namespace) -> None:
        """Run the selected CLI command."""
        self._init_app(args)
        handlers: dict[CLICommands, Callable[[argparse.Namespace], None]] = {
            CLICommands.ME: self._show_me,
            CLICommands.ISSUE: self._show_issue_command,
            CLICommands.CURRENT: self._show_current_issue_command,
            CLICommands.CLOSED: self._show_closed,
            CLICommands.CREATED: self._show_created,
            CLICommands.IN_PROGRESS: self._show_in_progress,
            CLICommands.REPORT: self._show_report,
        }
        try:
            handler = handlers[CLICommands(args.command)]
        except (KeyError, ValueError) as error:
            raise SystemExit(f"Unknown command: {args.command}") from error
        handler(args)

    def _init_app(self, args: argparse.Namespace) -> None:
        """Initialize Jira stats exporter."""
        if self._app is not None:
            return

        try:
            config = AppConfig.load(args.config)
            self._printer = CLIPrinter(config.cli)
            self._app = App.from_config(config)
            self._reporter = HTMLReporter(self._app.get_report_data)
        except Exception as e:
            print(f"[red]Failed to init app:\n{e!r}[/]")
            traceback.print_exception(e)
            exit(1)

    # COMMANDS

    def _show_me(self, _: argparse.Namespace) -> None:
        """Show current Jira user data."""
        payload = self.app.me()
        self._printer.print_json(payload)

    def _show_issue_command(self, args: argparse.Namespace) -> None:
        """Show Jira issue data for parsed CLI arguments."""
        self._show_issue(
            args.key,
            raw=args.raw,
            show_description=args.description,
        )

    def _show_current_issue_command(self, args: argparse.Namespace) -> None:
        """Show the current Jira issue for parsed CLI arguments."""
        self._show_issue(
            self._current_branch(),
            raw=args.raw,
            show_description=args.description,
            open_in_browser=args.open,
        )

    def _show_issue(
        self,
        key: str,
        raw: bool = False,
        show_description: bool = False,
        open_in_browser: bool = False,
    ) -> None:
        """Show Jira issue data."""
        issue = self.app.issue(key)
        if open_in_browser and issue.url:
            webbrowser.open(issue.url)

        if raw:
            self._printer.print_json(issue.raw)
            return

        self._printer.print_issue(issue, show_description=show_description)

    def _show_closed(self, args: argparse.Namespace) -> None:
        """Show closed issues."""
        date_range = self._resolve_date_range(args)
        issue_groups, team = self._show_for_users(
            args,
            lambda user: self.app.get_closed_issues(
                user,
                date_range,
                with_summary=args.issues,
            ),
            lambda issue_group: self._printer.print_issue_group(
                issue_group,
                show_details=args.issues,
            ),
        )

        if team:
            self._printer.print_team_summary(issue_groups)

    def _show_in_progress(self, args: argparse.Namespace) -> None:
        """Show in-progress issues."""
        self._show_for_users(
            args,
            self.app.get_in_progress_issues,
            lambda issue_group: self._printer.print_issue_group(
                issue_group,
                show_issues_number=False,
                show_metrics=False,
            ),
        )

    def _show_created(self, args: argparse.Namespace) -> None:
        """Show issues created by a user during a date range."""
        date_range = self._resolve_date_range(args)
        self._show_for_users(
            args,
            lambda user: self.app.get_created_issues(user, date_range),
            lambda issue_group: self._printer.print_issue_group(
                issue_group,
                show_metrics=False,
            ),
        )

    def _show_report(self, args: argparse.Namespace) -> None:
        """Create and open an HTML report."""
        date_range = self._resolve_date_range(args)
        users, _ = self._get_users_and_team(args)
        self._print_report_progress("Preparing report")
        report_path = self.reporter.create_report(
            users,
            date_range,
            progress=self._print_report_progress,
        ).resolve()
        print(f"[green]Report created: {report_path}[/]")
        self._print_report_progress("Opening report in browser")
        webbrowser.open(report_path.as_uri())

    @staticmethod
    def _print_report_progress(message: str) -> None:
        """Print one report generation progress stage."""
        print(f"[cyan]→[/] {message}")

    # HELPERS

    @staticmethod
    def _resolve_date_range(args: argparse.Namespace) -> DateRange:
        """Resolve and validate date range arguments."""
        try:
            return DateRange.resolve(**vars(args))
        except ValueError as error:
            raise SystemExit(str(error)) from error

    def _show_for_users(
        self,
        args: argparse.Namespace,
        loader: IssueGroupLoader,
        renderer: IssueGroupRenderer,
    ) -> tuple[list[IssueGroup], Team | None]:
        """Load and render issue groups for selected users."""
        users, team = self._get_users_and_team(args)
        issue_groups: list[IssueGroup] = []
        for index, user in enumerate(users):
            if index > 0:
                self._printer.print_separator()

            issue_group = loader(user)
            issue_groups.append(issue_group)
            renderer(issue_group)

        return issue_groups, team

    @staticmethod
    def _current_branch() -> str:
        """Return the current Git branch name."""
        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as error:
            raise SystemExit("Unable to determine the current Git branch") from error

        if not branch:
            raise SystemExit("No current Git branch is checked out")

        return branch

    def _get_users_and_team(
        self,
        args: argparse.Namespace,
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

        if team:
            self._printer.print_team(team)

        return users, team
