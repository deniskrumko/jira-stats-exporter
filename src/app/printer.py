import json

from rich import print
from rich.markup import escape
from rich.panel import Panel

from app.config import CLIConfig
from app.resources import Issue, IssueGroup
from core.cli_utils import print_stat
from core.utils import format_seconds, truncate
from teams import Team


class CLIPrinter:
    """Render Jira CLI output."""

    def __init__(self, config: CLIConfig) -> None:
        """Initialize class instance."""
        self._config = config

    def print_json(self, payload: object) -> None:
        """Print a payload as formatted JSON."""
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    def print_issue(self, issue: Issue, show_description: bool = False) -> None:
        """Print Jira issue details."""
        print_stat("Title", escape(issue.title or ""))
        print_stat("Assignee", escape(issue.assignee or ""))
        print_stat("Status", escape(issue.status or ""))
        print_stat("Labels", ", ".join(issue.labels))
        print_stat("URL", escape(issue.url or ""))
        if issue.epic_link:
            print_stat("Epic Link", escape(issue.epic_url or ""))
            print_stat("Epic Name", escape(issue.epic_name or ""))
        if show_description:
            print_stat("Description", escape(issue.description or ""))

    def print_team(self, team: Team) -> None:
        """Print a configured Jira team."""
        print(Panel.fit(f"[bold green]Team: {team}[/]", border_style="green"), end="\n\n")

    def print_issue_group(
        self,
        issue_group: IssueGroup,
        show_date_range: bool = True,
        show_user: bool = True,
        show_issues_number: bool = True,
        show_metrics: bool = True,
        show_details: bool = True,
    ) -> None:
        """Print Jira issue group statistics and details."""
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
                summary = truncate(issue.summary or "", self._config.max_summary_length)
                print(f"[cyan bold link={issue.url}]{issue.code}[/]: {summary}")

    def print_team_summary(self, issue_groups: list[IssueGroup]) -> None:
        """Print aggregate issue statistics for a team."""
        total_tasks = sum(issue_group.count for issue_group in issue_groups)
        total_ttm = sum(issue_group.total_ttm for issue_group in issue_groups)
        avg_ttm = format_seconds(total_ttm // total_tasks) if total_tasks else format_seconds(0)
        print(f"\n[bold green]Total tasks: {total_tasks}\nAverage TTM: {avg_ttm}[/]")

    @staticmethod
    def print_separator() -> None:
        """Print a separator between user results."""
        print()

    @staticmethod
    def _print_issues_number(issue_group: IssueGroup, display_name: str = "Issues") -> None:
        """Print the issue count and weekly rate."""
        value_color = "yellow not b"

        if issue_group.count == 0 and issue_group.date_range and issue_group.date_range.days >= 3:
            value_color = "red"
        elif issue_group.count > 3 and issue_group.date_range and issue_group.date_range.days <= 7:
            value_color = "green"

        line = str(issue_group.count)
        if issue_group.date_range and issue_group.issues_per_week:
            line += f" [dim]({issue_group.issues_per_week:.1f}/week)[/dim]"

        print_stat(display_name, line, value_color=value_color)
