from datetime import date
from typing import Any

from app.app import App
from core.date_ranges import DateRange
from jira import JQLClient
from teams import MockTeamsClient
from users import MockUsersClient, User


class FakeJiraAPIClient:
    """Provide Jira client responses for closed issue tests."""

    def __init__(self) -> None:
        """Initialize class instance."""
        self.search_calls: list[dict[str, Any]] = []

    def me(self) -> dict[str, Any]:
        """Return fake current user data."""
        return {"name": "krumko"}

    def issue(self, key: str) -> dict[str, Any]:
        """Return fake issue data."""
        return {"key": key}

    def search(
        self,
        jql: str,
        fields: list[str] | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Return fake Jira search pages."""
        self.search_calls.append(
            {
                "jql": jql,
                "fields": fields,
                "start_at": start_at,
                "max_results": max_results,
            }
        )
        return {
            "total": 2,
            "issues": [
                {
                    "key": "ML-1",
                    "fields": {
                        "summary": "Short issue summary",
                        "customfield_12602": 3600,
                        "customfield_12603": 1200,
                        "customfield_12604": 600,
                        "customfield_12605": 300,
                    },
                },
                {
                    "key": "ML-2",
                    "fields": {
                        "summary": "A" * 120,
                        "customfield_12602": 9000,
                        "customfield_12603": 2400,
                        "customfield_12604": 1800,
                        "customfield_12605": 900,
                    },
                },
            ],
        }

    def search_all(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int = 100,
    ) -> Any:
        """Return fake Jira search pages."""
        yield self.search(
            jql,
            fields=fields,
            start_at=0,
            max_results=max_results,
        )

    def issue_url(self, key: str) -> str:
        """Return a fake browser URL for a Jira issue."""
        return f"https://jira.example.test/browse/{key}"


class FakeCustomFieldsClient:
    """Provide custom fields behavior for closed issue tests."""

    def replace(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return payload without changes."""
        return payload

    def get_field_by_name(self, field_name: str) -> str:
        """Return a fake custom field ID."""
        return {
            "TTM": "customfield_12602",
            "Time in Progress": "customfield_12603",
            "Time in Review": "customfield_12604",
            "Time in Resolved": "customfield_12605",
        }.get(field_name, field_name)


def test_closed_returns_issue_links_and_average_ttm() -> None:
    """Return closed issue links and average TTM from Jira search results."""
    api_client = FakeJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=FakeCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"me": User(username="krumko")}),
        teams_client=MockTeamsClient({}),
    )
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31))

    issue_group = app.get_closed_issues("me", date_range)
    assert [issue.url for issue in issue_group.issues] == [
        "https://jira.example.test/browse/ML-1",
        "https://jira.example.test/browse/ML-2",
    ]
    assert issue_group.avg_time_in_status == {
        "TTM": 6300,
        "Time in Progress": 1800,
        "Time in Review": 1200,
        "Time in Resolved": 600,
    }

    assert api_client.search_calls[0]["fields"] == [
        "key",
        "summary",
        "customfield_12602",
        "customfield_12603",
        "customfield_12604",
        "customfield_12605",
    ]
    assert "Responsibles in (krumko)" in api_client.search_calls[0]["jql"]


def test_closed_resolves_configured_user_alias() -> None:
    """Resolve configured user aliases before building Jira queries."""
    api_client = FakeJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=FakeCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"arstan": User(username="turdubaev", aliases=["arstan"])}),
        teams_client=MockTeamsClient({}),
    )
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31))

    issue_group = app.get_closed_issues("arstan", date_range)

    assert issue_group.responsible == "turdubaev"
    assert "Responsibles in (turdubaev)" in api_client.search_calls[0]["jql"]
