from pathlib import Path

import pytest

from app.app import App
from jira import JiraAPIClient, JiraCustomFieldsClient, JQLClient


@pytest.fixture
def config(tmp_path: Path) -> Path:
    return _write_config(tmp_path)


@pytest.fixture
def app(config, jira_cf_client, jira_api_client) -> App:
    """Build an application without real Jira clients."""
    return App(
        api_client=jira_api_client,
        cf_client=jira_cf_client,
        jql_client=JQLClient(),
        config=config,
    )


def _write_config(tmp_path: Path) -> Path:
    """Write a test application config."""
    config = tmp_path / "config.toml"
    config.write_text(
        """
[api]
base_url = "https://jira.example.com"
api_token = "123"

[cli]
max_summary_length = 60

[teams.pl]
name = "Pupa And Lupa Group"
default = true
users = ["pupa", "lupa"]

[teams.kr]
name = "Krumko Productions"
users = ["krumko"]
""".strip()
    )
    return config


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
