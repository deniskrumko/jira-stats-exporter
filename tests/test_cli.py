from pathlib import Path

from app.cli import DEFAULT_TEAM_MARKER, CLIApp, build_parser
from app.resources import Issue


class FakeApp:
    """Provide issue data for CLI tests."""

    def issue(self, key: str) -> Issue:
        """Return a fake Jira issue."""
        return Issue(
            raw={
                "key": key,
                "fields": {
                    "summary": "Настройка выгрузки",
                    "assignee": {"name": "krumko"},
                    "status": {"name": "Открытая"},
                    "description": "Описание задачи",
                },
            },
            url=f"https://jira.example.test/browse/{key}",
        )


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


def test_parser_reads_issue_raw_flag() -> None:
    """Read raw output flag for issue command."""
    args = build_parser().parse_args(["issue", "ML-1234", "--raw"])

    assert args.key == "ML-1234"
    assert args.raw is True


def test_issue_command_prints_pretty_output_by_default(capsys) -> None:
    """Print formatted Jira issue details by default."""
    args = build_parser().parse_args(["issue", "ML-1234"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert "Title: Настройка выгрузки" in output
    assert "Assignee: krumko" in output
    assert "Status: Открытая" in output
    assert "URL: https://jira.example.test/browse/ML-1234" in output
    assert "Description: Описание задачи" in output


def test_issue_command_prints_raw_json(capsys) -> None:
    """Print raw Jira issue JSON when raw flag is enabled."""
    args = build_parser().parse_args(["issue", "ML-1234", "--raw"])

    CLIApp(FakeApp()).run(args)

    output = capsys.readouterr().out
    assert '"key": "ML-1234"' in output
    assert '"summary": "Настройка выгрузки"' in output
    assert "Title:" not in output
