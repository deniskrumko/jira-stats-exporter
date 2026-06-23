from collections.abc import Iterator
from typing import Any

from jira.client import ABCJiraAPIClient
from jira.custom_fields import ABCJiraCustomFieldsClient


class MockJiraAPIClient(ABCJiraAPIClient):
    """Provide Jira client responses for tests and local development."""

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
    ) -> Iterator[dict[str, Any]]:
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

    def fields(self) -> list[Any]:
        """Return fake Jira field metadata."""
        return []


class MockJiraCustomFieldsClient(ABCJiraCustomFieldsClient):
    """Provide custom fields behavior for tests and local development."""

    def get_fields(self) -> dict[str, str]:
        """Return fake Jira custom field mappings."""
        return {
            "customfield_12602": "TTM",
            "customfield_12603": "Time in Progress",
            "customfield_12604": "Time in Review",
            "customfield_12605": "Time in Resolved",
        }

    def replace(
        self,
        payload: dict,
        fields: dict[str, str] | None = None,
    ) -> dict:
        """Return payload without changes."""
        return payload

    def get_field_by_name(self, field_name: str) -> str:
        """Return a fake custom field ID."""
        name_to_field = {field_name: field_id for field_id, field_name in self.get_fields().items()}
        return name_to_field.get(field_name, field_name)
