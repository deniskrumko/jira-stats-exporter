from pathlib import Path
from subprocess import CompletedProcess

import pytest

from app.cli import DEFAULT_TEAM_MARKER, CLIApp, build_parser
from app.resources import Issue, IssueGroup
from core.date_ranges import DateRange
from reporter import MockReporterClient
from teams import Team
from users import User


class FakeApp:
    """Provide issue data for CLI tests."""

    def __init__(
        self,
        empty_closed: bool = False,
        empty_kpi: bool = False,
        with_epic: bool = True,
    ) -> None:
        """Initialize class instance."""
        self.created_calls: list[tuple[str, DateRange]] = []
        self.closed_calls: list[tuple[str, DateRange, bool]] = []
        self.kpi_calls: list[tuple[str, DateRange, bool]] = []
        self.in_progress_calls: list[str] = []
        self.empty_closed = empty_closed
        self.empty_kpi = empty_kpi
        self.with_epic = with_epic

    def me(self) -> dict[str, str]:
        """Return a fake current Jira user."""
        return {"name": "krumko"}

    def issue(self, key: str) -> Issue:
        """Return a fake Jira issue."""
        return Issue(
            raw={
                "key": key,
                "fields": {
                    "summary": "Report configuration",
                    "assignee": {"name": "krumko"},
                    "status": {"name": "Open"},
                    "labels": [],
                    "description": "Issue description",
                },
            },
            url=f"https://jira.example.test/browse/{key}",
            epic_link="ML-2161" if self.with_epic else None,
            epic_url="https://jira.example.test/browse/ML-2161" if self.with_epic else None,
            epic_name="Platform epic" if self.with_epic else None,
        )

    def get_created_issues(self, creator: str, date_range: DateRange) -> IssueGroup:
        """Return fake issues created by a user."""
        self.created_calls.append((creator, date_range))
        return IssueGroup(
            issues=[self.issue("ML-1234")],
            jql=f"created JQL for {creator}",
            user=User(username=creator),
            date_range=date_range,
        )

    def get_closed_issues(
        self,
        responsible: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return fake closed issues for a user."""
        self.closed_calls.append((responsible, date_range, with_summary))
        issues = [] if self.empty_closed else [self.issue("ML-1234")]
        return IssueGroup(
            issues=issues,
            jql=f"closed JQL for {responsible}",
            user=User(username=responsible),
            date_range=date_range,
            metrics={"TTM": [] if self.empty_closed else [3600]},
        )

    def get_in_progress_issues(self, assignee: str) -> IssueGroup:
        """Return fake in-progress issues for a user."""
        self.in_progress_calls.append(assignee)
        return IssueGroup(
            issues=[self.issue("ML-1234")],
            jql=f"in-progress JQL for {assignee}",
            user=User(username=assignee),
        )

    def get_kpi_tracked_issues(
        self,
        responsible: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return fake KPI-tracked issues for a user."""
        self.kpi_calls.append((responsible, date_range, with_summary))
        issues = [] if self.empty_kpi else [self.issue("ML-1234")]
        return IssueGroup(
            issues=issues,
            jql=f"KPI JQL for {responsible}",
            user=User(username=responsible),
            date_range=date_range,
            metrics={"TTM": [] if self.empty_kpi else [3600]},
        )

    def get_team(self, shortcut: str | None = None) -> Team:
        """Return a fake configured team."""
        if shortcut not in (None, "ml"):
            raise ValueError("Team was not found")
        return Team(name="ML team", users=["krumko", "pupa"], default=shortcut is None)


def test_parser_keeps_config_before_command() -> None:
    """Keep config path when it is specified before a command."""
    args = build_parser().parse_args(
        ["--config", "config.test.toml", "closed", "--team", "ml", "-m", "5"]
    )

    assert args.config == Path("config.test.toml")
    assert args.team == "ml"
    assert not hasattr(args, "issues")


def test_parser_reads_config_after_command() -> None:
    """Read config path when it is specified after a command."""
    args = build_parser().parse_args(
        ["closed", "--config", "config.test.toml", "--team", "-m", "5"]
    )

    assert args.config == Path("config.test.toml")
    assert args.team == DEFAULT_TEAM_MARKER


def test_parser_reads_issue_output_flags() -> None:
    """Read output flags for issue command."""
    args = build_parser().parse_args(["issue", "ML-1234", "--raw", "-d"])

    assert args.key == "ML-1234"
    assert args.raw is True
    assert args.description is True


def test_parser_reads_current_command_alias() -> None:
    """Read the current issue command alias."""
    args = build_parser().parse_args(["current", "-d"])

    assert args.command == "cur"
    assert args.description is True
    assert args.open is False


def test_parser_reads_created_user_and_date_range() -> None:
    """Read creator and explicit date range for the created command."""
    args = build_parser().parse_args(
        ["created", "--user", "krumko", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    assert args.command == "created"
    assert args.user == "krumko"
    assert args.from_date == "2026-05-01"
    assert args.to_date == "2026-05-31"


def test_parser_reads_created_team() -> None:
    """Read a configured team for the created command."""
    args = build_parser().parse_args(["created", "--team", "ml", "--month", "0"])

    assert args.team == "ml"


def test_parser_reads_kpi_user_and_date_range() -> None:
    """Read responsible user and explicit date range for the KPI command."""
    args = build_parser().parse_args(
        ["kpi", "--user", "krumko", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    assert args.command == "kpi"
    assert args.user == "krumko"
    assert args.from_date == "2026-05-01"
    assert args.to_date == "2026-05-31"


@pytest.mark.parametrize("command", ["closed", "kpi", "created", "inprogress"])
def test_parser_reads_jql_flag(command: str) -> None:
    """Enable generated JQL output for issue-list commands."""
    args = build_parser().parse_args([command, "--jql"])

    assert args.jql is True


@pytest.mark.parametrize("command", ["closed", "kpi", "created", "inprogress"])
@pytest.mark.parametrize("flag", ["-s", "--stats-only"])
def test_parser_reads_stats_only_flag(command: str, flag: str) -> None:
    """Enable statistics-only output for issue-list commands."""
    args = build_parser().parse_args([command, flag])

    assert args.stats_only is True


def test_parser_reads_report_team_and_date_range() -> None:
    """Read team and date range options for the report command."""
    args = build_parser().parse_args(["report", "--team", "ml", "--week", "0"])

    assert args.command == "report"
    assert args.team == "ml"
    assert args.user == "me"
    assert args.week == 0


def test_me_command_prints_current_user(capsys) -> None:
    """Dispatch and print the current user command."""
    args = build_parser().parse_args(["me"])

    CLIApp(FakeApp()).run(args)

    assert '"name": "krumko"' in capsys.readouterr().out


def test_issue_command_prints_pretty_output_by_default(capsys) -> None:
    """Print formatted Jira issue details by default."""
    args = build_parser().parse_args(["issue", "ML-1234"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "Title: Report configuration" in output
    assert "Assignee: krumko" in output
    assert "Status: Open" in output
    assert "URL: https://jira.example.test/browse/ML-1234" in output
    assert "Epic Link: https://jira.example.test/browse/ML-2161" in output
    assert "Epic Name: Platform epic" in output
    assert "Description:" not in output


def test_issue_command_prints_description_with_flag(capsys) -> None:
    """Print Jira issue description when requested."""
    args = build_parser().parse_args(["issue", "ML-1234", "-d"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "Description: Issue description" in output


def test_issue_command_hides_epic_when_issue_has_no_epic(capsys) -> None:
    """Do not print epic fields when an issue has no epic link."""
    args = build_parser().parse_args(["issue", "ML-1234"])

    CLIApp(FakeApp(with_epic=False)).run(args)

    output = capsys.readouterr().out
    assert "Epic Link:" not in output
    assert "Epic Name:" not in output


def test_issue_command_prints_raw_json(capsys) -> None:
    """Print raw Jira issue JSON when raw flag is enabled."""
    args = build_parser().parse_args(["issue", "ML-1234", "--raw"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert '"key": "ML-1234"' in output
    assert '"summary": "Report configuration"' in output
    assert "Title:" not in output


def test_current_issue_command_uses_git_branch(monkeypatch, capsys) -> None:
    """Show the issue that matches the current Git branch."""
    monkeypatch.setattr(
        "app.cli.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(args, 0, stdout="ML-1234\n"),
    )
    args = build_parser().parse_args(["cur"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "URL: https://jira.example.test/browse/ML-1234" in output


def test_current_issue_command_opens_issue_in_browser(monkeypatch) -> None:
    """Open the current issue URL in a browser when requested."""
    monkeypatch.setattr(
        "app.cli.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(args, 0, stdout="ML-1234\n"),
    )
    opened_urls = []
    monkeypatch.setattr("app.cli.webbrowser.open", opened_urls.append)
    args = build_parser().parse_args(["cur", "-o"])

    CLIApp(FakeApp()).run(args)

    assert opened_urls == ["https://jira.example.test/browse/ML-1234"]


def test_created_command_requests_and_prints_created_issues(capsys) -> None:
    """Request created issues for the selected user and date range."""
    app = FakeApp()
    args = build_parser().parse_args(
        ["created", "-u", "krumko", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    assert app.created_calls == [
        (
            "krumko",
            DateRange(start="2026-05-01", end="2026-05-31"),
        )
    ]
    output = capsys.readouterr().out
    assert "User: krumko\nDate Range: 2026-05-01 – 2026-05-31" in output
    assert "ML-1234" in output


def test_created_command_requests_issues_for_each_team_user(capsys) -> None:
    """Request created issues for every configured team user."""
    app = FakeApp()
    args = build_parser().parse_args(
        ["created", "--team", "ml", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    assert [creator for creator, _ in app.created_calls] == ["krumko", "pupa"]
    output = capsys.readouterr().out
    assert "Team: ML team" in output
    assert "User: krumko" in output
    assert "User: pupa" in output


def test_closed_command_requests_closed_issues(capsys) -> None:
    """Dispatch closed issues through the shared user workflow."""
    app = FakeApp()
    args = build_parser().parse_args(
        ["closed", "-u", "krumko", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    assert app.closed_calls == [
        (
            "krumko",
            DateRange(start="2026-05-01", end="2026-05-31"),
            True,
        )
    ]
    output = capsys.readouterr().out
    assert "User: krumko\nDate Range: 2026-05-01 – 2026-05-31" in output
    assert "Avg TTM: 1h 0m" in output
    assert "ML-1234" in output


def test_kpi_command_requests_kpi_tracked_issues(capsys) -> None:
    """Dispatch KPI-tracked issues through the shared user workflow."""
    app = FakeApp()
    args = build_parser().parse_args(
        ["kpi", "-u", "krumko", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    assert app.kpi_calls == [
        (
            "krumko",
            DateRange(start="2026-05-01", end="2026-05-31"),
            True,
        )
    ]
    output = capsys.readouterr().out
    assert "User: krumko\nDate Range: 2026-05-01 – 2026-05-31" in output
    assert "Avg TTM: 1h 0m" in output
    assert "ML-1234" in output


def test_in_progress_command_requests_in_progress_issues(capsys) -> None:
    """Dispatch in-progress issues through the shared user workflow."""
    app = FakeApp()
    args = build_parser().parse_args(["inprogress", "-u", "krumko"])

    CLIApp(app).run(args)

    assert app.in_progress_calls == ["krumko"]
    output = capsys.readouterr().out
    assert "Date Range:" not in output
    assert "ML-1234" in output


@pytest.mark.parametrize(
    "arguments",
    [
        ["closed", "--from", "2026-05-01", "--to", "2026-05-31"],
        ["kpi", "--from", "2026-05-01", "--to", "2026-05-31"],
        ["created", "--from", "2026-05-01", "--to", "2026-05-31"],
        ["inprogress"],
    ],
)
def test_stats_only_hides_issue_details(arguments: list[str], capsys) -> None:
    """Hide issue details while keeping command statistics."""
    args = build_parser().parse_args([*arguments, "--stats-only"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "User: me" in output
    assert "ML-1234" not in output


def test_stats_only_keeps_statistics(capsys) -> None:
    """Keep issue count and metrics in statistics-only output."""
    args = build_parser().parse_args(
        [
            "closed",
            "--from",
            "2026-05-01",
            "--to",
            "2026-05-31",
            "--stats-only",
        ]
    )

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "Date Range: 2026-05-01 – 2026-05-31" in output
    assert "Issues: 1" in output
    assert "Avg TTM: 1h 0m" in output


@pytest.mark.parametrize(
    ("arguments", "expected_jql"),
    [
        (["closed", "--from", "2026-05-01", "--to", "2026-05-31"], "closed JQL for me"),
        (["kpi", "--from", "2026-05-01", "--to", "2026-05-31"], "KPI JQL for me"),
        (
            ["created", "--from", "2026-05-01", "--to", "2026-05-31"],
            "created JQL for me",
        ),
        (["inprogress"], "in-progress JQL for me"),
    ],
)
def test_issue_list_commands_print_jql_at_end(
    arguments: list[str],
    expected_jql: str,
    capsys,
) -> None:
    """Print the generated JQL after the regular command output."""
    args = build_parser().parse_args([*arguments, "--jql"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "JQL:" in output
    assert output.rstrip().endswith(expected_jql)


def test_closed_team_with_no_issues_prints_zero_average(capsys) -> None:
    """Print zero team average when no team member closed an issue."""
    app = FakeApp(empty_closed=True)
    args = build_parser().parse_args(
        ["closed", "--team", "ml", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    output = capsys.readouterr().out
    assert "Total tasks: 0" in output
    assert "Average TTM: 0h 0m" in output


def test_kpi_team_with_no_issues_prints_zero_average(capsys) -> None:
    """Print zero team average when no team member has a KPI-tracked issue."""
    app = FakeApp(empty_kpi=True)
    args = build_parser().parse_args(
        ["kpi", "--team", "ml", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(app).run(args)

    assert [responsible for responsible, _, _ in app.kpi_calls] == ["krumko", "pupa"]
    output = capsys.readouterr().out
    assert "Total tasks: 0" in output
    assert "Average TTM: 0h 0m" in output


def test_team_jql_output_labels_each_user(capsys) -> None:
    """Label every generated team JQL query with its resolved user."""
    args = build_parser().parse_args(
        [
            "created",
            "--team",
            "ml",
            "--from",
            "2026-05-01",
            "--to",
            "2026-05-31",
            "--jql",
        ]
    )

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "JQL (krumko):\ncreated JQL for krumko" in output
    assert output.rstrip().endswith("JQL (pupa):\ncreated JQL for pupa")


def test_report_command_creates_and_opens_current_user_report(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """Create a current-user report and open its file URL."""
    report_path = tmp_path / "jira-report.html"
    reporter = MockReporterClient(report_path)
    opened_urls: list[str] = []
    monkeypatch.setattr("app.cli.webbrowser.open", opened_urls.append)
    args = build_parser().parse_args(["report", "--from", "2026-05-01", "--to", "2026-05-31"])

    CLIApp(FakeApp(), reporter).run(args)

    date_range = DateRange(start="2026-05-01", end="2026-05-31")
    assert reporter.calls == [(["me"], date_range)]
    assert opened_urls == [report_path.resolve().as_uri()]
    output = capsys.readouterr().out
    assert "Preparing report" in output
    assert "Generating report" in output
    assert "jira-report.html" in output
    assert "Opening report in browser" in output


def test_report_command_uses_configured_team(tmp_path: Path, monkeypatch) -> None:
    """Create a report for every selected team user."""
    reporter = MockReporterClient(tmp_path / "jira-report.html")
    monkeypatch.setattr("app.cli.webbrowser.open", lambda _url: None)
    args = build_parser().parse_args(
        ["report", "--team", "ml", "--from", "2026-05-01", "--to", "2026-05-31"]
    )

    CLIApp(FakeApp(), reporter).run(args)

    assert reporter.calls[0][0] == ["krumko", "pupa"]
