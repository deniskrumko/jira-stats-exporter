from collections.abc import Iterator
from typing import Any

import httpx

from jira.config import JiraAPIConfig


class JiraAPIClient:
    """HTTP client for Jira REST API endpoints used by the exporter."""

    def __init__(self, config: JiraAPIConfig | None = None) -> None:
        """Initialize class instance."""
        self._config = config or JiraAPIConfig.from_env()

    def me(self) -> dict[str, Any]:
        """Fetch information about the authenticated Jira user."""
        return self._get("/rest/api/2/myself")

    def issue(self, key: str) -> dict[str, Any]:
        """Fetch a Jira issue by its issue key."""
        return self._get(f"/rest/api/2/issue/{key}")

    def search(
        self,
        jql: str,
        fields: list[str] | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Search Jira issues using JQL."""
        payload: dict[str, Any] = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if fields is not None:
            payload["fields"] = fields
        return self._post("/rest/api/2/search", payload)

    def search_all(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int = 100,
    ) -> Iterator[dict[str, Any]]:
        """Yield all Jira search pages using JQL."""
        start_at = 0
        while True:
            payload = self.search(
                jql,
                fields=fields,
                start_at=start_at,
                max_results=max_results,
            )
            yield payload

            total = payload.get("total")
            if not isinstance(total, int):
                raise RuntimeError("Unexpected Jira search response")
            start_at += max_results
            if start_at >= total:
                return

    def issue_url(self, key: str) -> str:
        """Build a browser URL for a Jira issue key."""
        return f"{self._config.base_url}/browse/{key}"

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

    def _get_json(self, url: str) -> dict | list:
        """Fetch a Jira endpoint and return the decoded JSON response."""
        with httpx.Client(
            base_url=self._config.base_url,
            headers={"Authorization": f"Bearer {self._config.api_token}"},
            timeout=30.0,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Post to a Jira endpoint and require a JSON object response."""
        with httpx.Client(
            base_url=self._config.base_url,
            headers={"Authorization": f"Bearer {self._config.api_token}"},
            timeout=30.0,
        ) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            response_payload = response.json()
            if not isinstance(response_payload, dict):
                raise RuntimeError(f"Unexpected Jira response for {url}")
            return response_payload
