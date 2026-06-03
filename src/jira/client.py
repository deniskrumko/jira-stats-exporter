from typing import Any

import httpx

from jira.config import JiraConfig


class JiraClient:
    def __init__(self, config: JiraConfig | None = None) -> None:
        self._config = config or JiraConfig.from_env()

    def me(self) -> dict[str, Any]:
        return self._get("/rest/api/2/myself")

    def _get(self, url: str) -> dict[str, Any]:
        with httpx.Client(
            base_url=self._config.base_url,
            headers={"Authorization": f"Bearer {self._config.api_token}"},
            timeout=30.0,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
