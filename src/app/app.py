from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.resources import Issue, IssueGroup, IssueStatus
from core.date_ranges import DateRange
from core.utils import avg
from jira import JiraAPIClient, JiraCustomFieldsClient, JQLClient
from teams import ABCTeamsClient, Team, TeamsClient
from users import ABCUsersClient, UsersClient

from .resources import TIME_METRICS


class App:
    """Run application business logic."""

    def __init__(
        self,
        api_client: JiraAPIClient,
        cf_client: JiraCustomFieldsClient,
        jql_client: JQLClient,
        users_client: ABCUsersClient,
        teams_client: ABCTeamsClient,
    ) -> None:
        """Initialize class instance."""
        self._api_client = api_client
        self._cf_client = cf_client
        self._jql_client = jql_client
        self._users_client = users_client
        self._teams_client = teams_client

    @classmethod
    def from_config(cls, config: Path | AppConfig | None = None) -> "App":
        """Create an application from config."""
        if not isinstance(config, AppConfig):
            config = AppConfig.load(config)

        api_client = JiraAPIClient.from_config(config.api)
        return cls(
            api_client=api_client,
            cf_client=JiraCustomFieldsClient(api_client),
            jql_client=JQLClient(),
            users_client=UsersClient(api_client, config.users),
            teams_client=TeamsClient(config.teams),
        )

    # Public methods

    def me(self) -> dict[str, Any]:
        """Get information about the authenticated Jira user."""
        return self._api_client.me()

    def issue(self, key: str, replace_custom_fields: bool = True) -> dict[str, Any]:
        """Get Jira issue data with custom field IDs replaced by field names."""
        response = self._api_client.issue(key)
        if replace_custom_fields:
            return self._cf_client.replace(response)

        return response

    def get_team(self, shortcut: str | None = None) -> Team:
        """Get team by shortcut name."""
        return self._teams_client.get_team(shortcut)

    @property
    def default_team(self) -> Team:
        """Return configured default team."""
        return self._teams_client.default_team

    def get_closed_issues(
        self,
        responsible: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return closed issues for a responsible user during a date range."""
        user = self._users_client.get_user(responsible)
        username = user.username
        jql = self._jql_client.closed_issues(username, date_range)

        fields = ["key"]
        if with_summary:
            fields.append("summary")

        metric_fields = {
            metric_name: self._cf_client.get_field_by_name(metric_name)
            for metric_name in TIME_METRICS
        }
        fields.extend(metric_fields.values())

        metric_values: dict[str, list[int]] = {metric_name: [] for metric_name in TIME_METRICS}
        issue_results: list[Issue] = []

        for payload in self._api_client.search_all(jql, fields=fields):
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
                            url=self._api_client.issue_url(key),
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

        return IssueGroup(
            responsible=username,
            date_range=date_range,
            issues=issue_results,
            avg_time_in_status={
                metric_name: avg(values) for metric_name, values in metric_values.items()
            },
        )
