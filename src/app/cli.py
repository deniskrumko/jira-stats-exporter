import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from app.app import JiraStatsExporter

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

    return parser


def main() -> None:
    """Run the Jira stats exporter CLI."""
    load_dotenv(DEFAULT_ENV_PATH)

    args = build_parser().parse_args()
    app = JiraStatsExporter()

    # Show current user
    if args.command == "me":
        payload = app.me()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.command == "issue":
        payload = app.issue(args.key)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
