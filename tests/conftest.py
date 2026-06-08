import pytest

from app.app import App
from jira import JiraAPIClient, JiraCustomFieldsClient, JQLClient
from teams import MockTeamsClient, Team
from users import MockUsersClient, User


@pytest.fixture
def app(jira_cf_client, jira_api_client) -> App:
    """Build an application without real Jira clients."""
    return App(
        api_client=jira_api_client,
        cf_client=jira_cf_client,
        jql_client=JQLClient(),
        users_client=MockUsersClient({"me": User(username="krumko")}),
        teams_client=MockTeamsClient(
            {
                "pl": Team(name="Pupa And Lupa Group", users=["pupa", "lupa"], default=True),
                "kr": Team(name="Krumko Productions", users=["krumko"]),
            }
        ),
    )


@pytest.fixture
def jira_cf_client() -> JiraCustomFieldsClient:
    return JiraCustomFieldsClient(
        custom_fields={
            "customfield_12602": "TTM",
            "summary": "Summary",
        }
    )


@pytest.fixture
def jira_api_client() -> JiraAPIClient:
    return JiraAPIClient(
        base_url="https://jira.example.com",
        api_token="123",
    )
