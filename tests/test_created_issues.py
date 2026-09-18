from datetime import date

from app.app import App
from core.date_ranges import DateRange
from jira import JQLClient, MockJiraAPIClient, MockJiraCustomFieldsClient
from teams import MockTeamsClient
from users import MockUsersClient, User


def test_created_returns_issues_for_resolved_user_and_date_range() -> None:
    """Return issues created by the resolved user during a date range."""
    api_client = MockJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=MockJiraCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"arstan": User(username="turdubaev", aliases=["arstan"])}),
        teams_client=MockTeamsClient({}),
    )
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31))

    issue_group = app.get_created_issues("arstan", date_range)

    assert [issue.code for issue in issue_group.issues] == ["ML-1", "ML-2"]
    assert issue_group.user == User(username="turdubaev", aliases=["arstan"])
    assert issue_group.date_range == date_range
    assert issue_group.metrics is None
    assert api_client.search_calls[0]["fields"] == ["key", "summary"]
    assert api_client.search_calls[0]["jql"] == (
        'creator in (turdubaev)\nAND created >= "2026-05-01"\nAND created < "2026-06-01"'
    )
    assert issue_group.jql == api_client.search_calls[0]["jql"]
