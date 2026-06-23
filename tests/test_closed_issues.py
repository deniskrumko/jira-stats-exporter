from datetime import date

from app.app import App
from core.date_ranges import DateRange
from jira import JQLClient, MockJiraAPIClient, MockJiraCustomFieldsClient
from teams import MockTeamsClient
from users import MockUsersClient, User


def test_closed_returns_issue_links_and_average_ttm() -> None:
    """Return closed issue links and average TTM from Jira search results."""
    api_client = MockJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=MockJiraCustomFieldsClient(),
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
    api_client = MockJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=MockJiraCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"arstan": User(username="turdubaev", aliases=["arstan"])}),
        teams_client=MockTeamsClient({}),
    )
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31))

    issue_group = app.get_closed_issues("arstan", date_range)

    assert issue_group.user == User(username="turdubaev", aliases=["arstan"])
    assert "Responsibles in (turdubaev)" in api_client.search_calls[0]["jql"]
