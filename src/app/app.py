from functools import cached_property
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.resources import Issue, Issues, IssueStatus, Team
from core.date_ranges import DateRange
from core.utils import avg
from jira import JiraAPIClient, JiraCustomFieldsClient, JQLClient

from .resources import TIME_METRICS


class App:
    """Run application business logic."""

    def __init__(
        self,
        client: JiraAPIClient | None = None,
        custom_fields_client: JiraCustomFieldsClient | None = None,
        jql_client: JQLClient | None = None,
        config: Path | AppConfig | None = None,
    ) -> None:
        """Initialize class instance."""
        self._api = client or JiraAPIClient()
        self._custom_fields_client = custom_fields_client or JiraCustomFieldsClient()
        self._jql_client = jql_client or JQLClient()

        self._config = self._load_config(config)
        self.teams = self._build_teams()

    # Public methods

    def me(self) -> dict[str, Any]:
        """Get information about the authenticated Jira user."""
        return self._api.me()

    def issue(self, key: str) -> dict[str, Any]:
        """Get Jira issue data with custom field IDs replaced by field names."""
        payload = self._api.issue(key)
        return self._custom_fields_client.replace(payload)

    def get_team(self, shortcut: str | None = None) -> Team:
        """Get team by shortcut name."""
        if shortcut is None:
            return self.default_team

        team = self.teams.get(shortcut)
        if team is None:
            raise ValueError(f"Team was not found by shortcut: {shortcut}")

        return team

    @cached_property
    def default_team(self) -> Team:
        """Return configured default team."""
        for team in self.teams.values():
            if team.default:
                return team

        raise ValueError("Default team is not configured")

    def get_closed_issues(
        self,
        responsible: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> Issues:
        """Return closed issues for a responsible user during a date range."""
        username = self._resolve_user(responsible)
        jql = self._jql_client.closed_issues(username, date_range)

        fields = ["key"]
        if with_summary:
            fields.append("summary")

        metric_fields = {
            metric_name: self._custom_fields_client.get_field_by_name(metric_name)
            for metric_name in TIME_METRICS
        }
        fields.extend(metric_fields.values())

        metric_values: dict[str, list[int]] = {metric_name: [] for metric_name in TIME_METRICS}
        issue_results: list[Issue] = []

        for payload in self._api.search_all(jql, fields=fields):
            issues = payload.get("issues")
            if not isinstance(issues, list):
                raise RuntimeError("Unexpected Jira search response")

            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                key = issue.get("key")
                fields = issue.get("fields")
                if not isinstance(fields, dict):
                    raise RuntimeError("Unexpected Jira search response")
                if isinstance(key, str):
                    summary = fields.get("summary")
                    issue_results.append(
                        Issue(
                            url=self._api.issue_url(key),
                            summary=summary if isinstance(summary, str) else None,
                            status=IssueStatus.CLOSED,
                        )
                    )

                for metric_name, field_name in metric_fields.items():
                    value = fields.get(field_name)
                    if value is None:
                        continue

                    if not isinstance(value, int):
                        raise ValueError(f"Unexpected Jira field {field_name}: {value}")
                    metric_values[metric_name].append(value)

        return Issues(
            responsible=username,
            date_range=date_range,
            issues=issue_results,
            avg_time_in_status={
                metric_name: avg(values) for metric_name, values in metric_values.items()
            },
        )

    # Private methods

    def _build_teams(self) -> dict[str, Team]:
        """Build teams from config."""
        return {
            team.shortcut: Team(
                name=team.name,
                shortcut=team.shortcut,
                users=team.users,
                default=team.default,
            )
            for team in self._config.teams
        }

    def _resolve_user(self, username: str) -> str:
        """Resolve the special user alias into a Jira username."""
        if username != "me":
            return username

        name = self.me().get("name")
        if not name or not isinstance(name, str):
            raise RuntimeError("Unable to resolve current Jira user")

        return name

    def _load_config(self, config: Path | AppConfig | None) -> AppConfig:
        """Load application config from a path or return a provided config."""
        if isinstance(config, AppConfig):
            return config

        return AppConfig.load(config)
