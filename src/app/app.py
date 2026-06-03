from typing import Any

from custom_fields import JiraCustomFieldsClient
from jira import JiraAPIClient


class JiraStatsExporter:
    """Coordinate Jira API access and response post-processing."""

    def __init__(
        self,
        client: JiraAPIClient | None = None,
        custom_fields_client: JiraCustomFieldsClient | None = None,
    ) -> None:
        """Initialize class instance."""
        self._client = client or JiraAPIClient()
        self._custom_fields_client = custom_fields_client or JiraCustomFieldsClient()

    def me(self) -> dict[str, Any]:
        """Return information about the authenticated Jira user."""
        return self._client.me()

    def issue(self, key: str) -> dict[str, Any]:
        """Return Jira issue data with custom field IDs replaced by field names."""
        payload = self._client.issue(key)
        return self._custom_fields_client.replace(payload)
