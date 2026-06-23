from app.app import App
from app.resources import Issue
from jira import JQLClient, MockJiraAPIClient, MockJiraCustomFieldsClient
from teams import MockTeamsClient
from users import MockUsersClient, User


def test_app_issue_returns_issue_with_raw_payload() -> None:
    """Return Jira issue model with raw payload and derived fields."""
    app = App(
        api_client=MockJiraAPIClient(),
        cf_client=MockJiraCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"me": User(username="krumko")}),
        teams_client=MockTeamsClient({}),
    )

    issue = app.issue("ML-1234")

    assert isinstance(issue, Issue)
    assert issue.raw["key"] == "ML-1234"
    assert issue.title == "Fake issue summary"
    assert issue.assignee == "krumko"
    assert issue.status == "Open"
    assert issue.url == "https://jira.example.test/browse/ML-1234"
    assert issue.description == "Fake issue description"
