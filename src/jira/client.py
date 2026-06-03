from typing import Any

import httpx

from jira.config import JiraConfig


class JiraAPIClient:
    """HTTP client for Jira REST API endpoints used by the exporter."""

    def __init__(self, config: JiraConfig | None = None) -> None:
        """Initialize class instance."""
        self._config = config or JiraConfig.from_env()

    def me(self) -> dict[str, Any]:
        """Fetch information about the authenticated Jira user."""
        return self._get("/rest/api/2/myself")

    def issue(self, key: str) -> dict[str, Any]:
        """Fetch a Jira issue by its issue key."""
        return self._get(f"/rest/api/2/issue/{key}")

    def fields(self) -> list[Any]:
        """Fetch Jira field metadata."""
        fields = self._get_json("/rest/api/2/field")
        if not isinstance(fields, list):
            raise RuntimeError("Unexpected Jira fields response")
        return fields

    def _get(self, url: str) -> dict[str, Any]:
        """Fetch a Jira endpoint and require a JSON object response."""
        payload = self._get_json(url)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Unexpected Jira response for {url}")
        return payload

    def _get_json(self, url: str) -> Any:
        """Fetch a Jira endpoint and return the decoded JSON response."""
        with httpx.Client(
            base_url=self._config.base_url,
            headers={"Authorization": f"Bearer {self._config.api_token}"},
            timeout=30.0,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
