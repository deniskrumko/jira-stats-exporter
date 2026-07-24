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

    in_progress_parser = subparsers.add_parser(
        CLICommands.IN_PROGRESS,
        help="Show in-progress Jira issue links",
    )
    add_config_argument(in_progress_parser, argparse.SUPPRESS)
    in_progress_parser.add_argument(
        "-u",
        "--user",
        default="me",
        help="Jira responsible username or 'me'",
    )
    in_progress_parser.add_argument(
        "-t",
        "--team",
        nargs="?",
        const=DEFAULT_TEAM_MARKER,
        help="Use configured team users, optionally by shortcut",
    )

    return parser
