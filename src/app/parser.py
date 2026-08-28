import argparse
from pathlib import Path

from .resources import DEFAULT_TEAM_MARKER, CLICommands


def add_config_argument(
    parser: argparse.ArgumentParser,
    default: Path | str | None = None,
) -> None:
    """Add the shared config path option to an argument parser."""
    parser.add_argument(
        "--config",
        default=default,
        type=Path,
        help="Path to the Jira stats exporter TOML config",
    )


def add_issue_output_arguments(parser: argparse.ArgumentParser) -> None:
    """Add Jira issue output options to a command parser."""
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw Jira issue JSON",
    )
    parser.add_argument(
        "-d",
        "--description",
        action="store_true",
        help="Show Jira issue description",
    )


def add_user_argument(parser: argparse.ArgumentParser, role: str) -> None:
    """Add a Jira username option to a command parser."""
    parser.add_argument(
        "-u",
        "--user",
        default="me",
        help=f"Jira {role} username or 'me'",
    )


def add_team_argument(parser: argparse.ArgumentParser) -> None:
    """Add a configured team option to a command parser."""
    parser.add_argument(
        "-t",
        "--team",
        nargs="?",
        const=DEFAULT_TEAM_MARKER,
        help="Use configured team users, optionally by shortcut",
    )


def add_date_range_arguments(parser: argparse.ArgumentParser) -> None:
    """Add date range options to a command parser."""
    parser.add_argument(
        "-w",
        "--week",
        type=int,
        help="ISO week number or negative relative week",
    )
    parser.add_argument(
        "-q",
        "--quarter",
        type=int,
        help="Quarter number or negative relative quarter",
    )
    parser.add_argument(
        "-m",
        "--month",
        type=int,
        help="Month number or negative relative month",
    )
    parser.add_argument(
        "-d",
        "--day",
        type=int,
        help="Day of year or negative relative day",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        help="Range start date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        help="Range end date in YYYY-MM-DD",
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        help="Year for positive week, month, or day",
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
        subparsers.add_parser(
            CLICommands.ME,
            help="Show current Jira user",
        ),
        argparse.SUPPRESS,
    )

    issue_parser = subparsers.add_parser(
        CLICommands.ISSUE,
        help="Show Jira issue data",
    )
    add_config_argument(issue_parser, argparse.SUPPRESS)
    issue_parser.add_argument(
        "key",
        help="Jira issue key, for example ML-1234",
    )
    add_issue_output_arguments(issue_parser)

    current_parser = subparsers.add_parser(
        CLICommands.CURRENT,
        aliases=["current"],
        help="Show Jira issue for the current Git branch",
    )
    current_parser.set_defaults(command=CLICommands.CURRENT)
    add_config_argument(current_parser, argparse.SUPPRESS)
    add_issue_output_arguments(current_parser)
    current_parser.add_argument(
        "-o",
        "--open",
        action="store_true",
        help="Open the Jira issue in a browser",
    )

    closed_parser = subparsers.add_parser(
        CLICommands.CLOSED,
        help="Show closed Jira issue links",
    )

    add_config_argument(closed_parser, argparse.SUPPRESS)
    add_user_argument(closed_parser, "responsible")
    add_team_argument(closed_parser)
    add_date_range_arguments(closed_parser)

    created_parser = subparsers.add_parser(
        CLICommands.CREATED,
        help="Show Jira issues created by a user",
    )
    add_config_argument(created_parser, argparse.SUPPRESS)
    add_user_argument(created_parser, "creator")
    add_team_argument(created_parser)
    add_date_range_arguments(created_parser)

    in_progress_parser = subparsers.add_parser(
        CLICommands.IN_PROGRESS,
        help="Show in-progress Jira issue links",
    )
    add_config_argument(in_progress_parser, argparse.SUPPRESS)
    add_user_argument(in_progress_parser, "responsible")
    add_team_argument(in_progress_parser)

    report_parser = subparsers.add_parser(
        CLICommands.REPORT,
        help="Create and open an HTML Jira report",
    )
    add_config_argument(report_parser, argparse.SUPPRESS)
    add_user_argument(report_parser, "report user")
    add_team_argument(report_parser)
    add_date_range_arguments(report_parser)

    return parser
