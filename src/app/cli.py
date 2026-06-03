import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from jira import JiraClient

DEFAULT_ENV_PATH = Path.home() / ".secrets" / "jira-stats-exporter" / ".env"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Export statistics from Atlassian Jira",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("me", help="Show current Jira user")
    return parser


def main() -> None:
    load_dotenv(DEFAULT_ENV_PATH)

    args = build_parser().parse_args()
    client = JiraClient()

    # Show current user
    if args.command == "me":
        payload = client.me()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
