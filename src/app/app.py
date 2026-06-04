from typing import Any

from app.resources import ClosedIssue, ClosedIssuesStats
from core.date_ranges import DateRange
from core.utils import avg
from jira import JiraAPIClient, JiraCustomFieldsClient, JQLClient

TIME_METRICS = (
    "TTM",
    "Time in Progress",
    "Time in Review",
    "Time in Resolved",
)
ISSUE_SUMMARY_MAX_LENGTH = 60


class JiraStatsExporter:
    """Coordinate Jira API access and response post-processing."""

    def __init__(
        self,
        client: JiraAPIClient | None = None,
        custom_fields_client: JiraCustomFieldsClient | None = None,
        jql_client: JQLClient | None = None,
    ) -> None:
        """Initialize class instance."""
        self._client = client or JiraAPIClient()
        self._custom_fields_client = custom_fields_client or JiraCustomFieldsClient()
        self._jql_client = jql_client or JQLClient()

    def me(self) -> dict[str, Any]:
        """Return information about the authenticated Jira user."""
        return self._client.me()

    def issue(self, key: str) -> dict[str, Any]:
        """Return Jira issue data with custom field IDs replaced by field names."""
        payload = self._client.issue(key)
        return self._custom_fields_client.replace(payload)

    def closed(
        self, responsible: str, date_range: DateRange, with_summary: bool = True
    ) -> ClosedIssuesStats:
        """Return closed issue stats for a responsible user during a date range."""
        username = self._resolve_responsible(responsible)
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
        issues_stats: list[ClosedIssue] = []

        for payload in self._client.search_all(jql, fields=fields):
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
                    issues_stats.append(
                        ClosedIssue(
                            url=self._client.issue_url(key),
                            summary=_trim_summary(fields.get("summary")),
                        )
                    )

                for metric_name, field_name in metric_fields.items():
                    value = fields.get(field_name)
                    if value is None:
                        continue

                    if not isinstance(value, int):
                        raise ValueError(f"Unexpected Jira field {field_name}: {value}")
                    metric_values[metric_name].append(value)

        return ClosedIssuesStats(
            responsible=username,
            date_range=date_range,
            issues=issues_stats,
            avg_time_seconds={
                metric_name: avg(values) for metric_name, values in metric_values.items()
            },
        )

    def _resolve_responsible(self, responsible: str) -> str:
        """Resolve the special responsible alias into a Jira username."""
        if responsible != "me":
            return responsible

        name = self.me().get("name")
        if not name or not isinstance(name, str):
            raise RuntimeError("Unable to resolve current Jira user")

        return name


def _trim_summary(value: str | None) -> str | None:
    """Return a trimmed issue summary."""
    if not isinstance(value, str):
        return None
    if len(value) <= ISSUE_SUMMARY_MAX_LENGTH:
        return value
    return f"{value[:ISSUE_SUMMARY_MAX_LENGTH]}..."
