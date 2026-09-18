from pathlib import Path
from typing import Any, cast

from app.config import AppConfig
from app.resources import Issue, IssueGroup
from core.date_ranges import DateRange
from jira import (
    ABCJiraAPIClient,
    ABCJiraCustomFieldsClient,
    JiraAPIClient,
    JiraCustomFieldsClient,
    JQLClient,
)
from reporter import ReportProgress, UserReport
from teams import ABCTeamsClient, Team, TeamsClient
from users import ABCUsersClient, User, UsersClient

from .resources import TIME_METRICS


class App:
    """Run application business logic."""

    def __init__(
        self,
        api_client: ABCJiraAPIClient,
        cf_client: ABCJiraCustomFieldsClient,
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
        self._epic_names: dict[str, str | None] = {}

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

    def issue(self, key: str, replace_custom_fields: bool = True) -> Issue:
        """Get Jira issue data with custom field IDs replaced by field names."""
        issue = self._api_client.issue(key)
        if replace_custom_fields:
            issue.raw = self._cf_client.replace(issue.raw)
            result = Issue(raw=issue.raw, url=issue.url)
            fields = issue.raw.get("fields")
            if isinstance(fields, dict):
                epic_link = fields.get("Epic Link")
                if epic_link is not None and not isinstance(epic_link, str):
                    raise ValueError(f"Unexpected Jira field Epic Link: {epic_link}")
                self._attach_epic(result, epic_link)
                self._attach_parent(result, fields.get("parent"))
            return result

        return issue

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
        jql = self._jql_client.closed_issues(user, date_range)
        fields = self._get_fields(with_summary)
        return self._get_issue_group(jql, fields, user=user)

    def get_in_progress_issues(
        self,
        assignee: str,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return closed issues for a responsible user during a date range."""
        user = self._users_client.get_user(assignee)
        jql = self._jql_client.in_progress_issues(user)
        fields = self._get_fields(with_summary)
        return self._get_issue_group(jql, fields, user=user)

    def get_kpi_tracked_issues(
        self,
        responsible: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return KPI-tracked issues for a responsible user during a date range."""
        user = self._users_client.get_user(responsible)
        jql = self._jql_client.kpi_tracked_issues(user, date_range)
        fields = self._get_fields(with_summary)
        return self._get_issue_group(jql, fields, user=user)

    def get_created_issues(
        self,
        creator: str,
        date_range: DateRange,
        with_summary: bool = True,
    ) -> IssueGroup:
        """Return issues created by a user during a date range."""
        user = self._users_client.get_user(creator)
        jql = self._jql_client.created_issues(user, date_range)
        fields = self._get_fields(with_summary, with_metrics=False)
        return self._get_issue_group(
            jql,
            fields,
            user=user,
            date_range=date_range,
            with_metrics=False,
        )

    def get_report_data(
        self,
        username: str,
        date_range: DateRange,
        progress: ReportProgress | None = None,
    ) -> UserReport:
        """Return complete categorized issue data for one report user."""
        user = self._users_client.get_user(username)
        fields = self._get_fields(with_details=True)
        epic_field = self._cf_client.get_field_by_name("Epic Link")
        self._notify_report_progress(progress, user, "Loading closed issues")
        closed = self._get_issue_group(
            self._jql_client.closed_issues(user, date_range),
            fields,
            user=user,
            date_range=date_range,
            epic_field=epic_field,
        )
        self._notify_report_progress(progress, user, "Loading KPI tracked issues")
        kpi = self._get_issue_group(
            self._jql_client.kpi_tracked_issues(user, date_range),
            fields,
            user=user,
            date_range=date_range,
            epic_field=epic_field,
        )
        self._notify_report_progress(progress, user, "Loading in-progress issues")
        in_progress = self._get_issue_group(
            self._jql_client.in_progress_issues(user),
            fields,
            user=user,
            epic_field=epic_field,
        )
        self._notify_report_progress(progress, user, "Loading created issues")
        created = self._get_issue_group(
            self._jql_client.created_issues(user, date_range),
            fields,
            user=user,
            date_range=date_range,
            epic_field=epic_field,
        )
        return UserReport(
            user=user,
            closed=closed,
            kpi=kpi,
            in_progress=in_progress,
            created=created,
        )

    @staticmethod
    def _notify_report_progress(
        progress: ReportProgress | None,
        user: User,
        stage: str,
    ) -> None:
        """Send progress for one user report data stage."""
        if progress is not None:
            progress(f"{user.username}: {stage}")

    def _get_fields(
        self,
        with_summary: bool = True,
        with_metrics: bool = True,
        with_details: bool = False,
    ) -> list[str]:
        """Return Jira fields needed for an issue search."""
        fields = ["key"]
        if with_summary:
            fields.append("summary")

        if with_details:
            fields.extend(
                [
                    "description",
                    "status",
                    "labels",
                    "assignee",
                    "creator",
                    "parent",
                    self._cf_client.get_field_by_name("Epic Link"),
                ]
            )

        if with_metrics:
            fields.extend(self._get_metric_fields().values())

        return fields

    def _get_metric_fields(self) -> dict[str, str]:
        return {
            metric_name: self._cf_client.get_field_by_name(metric_name)
            for metric_name in TIME_METRICS
        }

    def _get_issue_group(
        self,
        jql: str,
        fields: list[str],
        *,
        user: User | None = None,
        date_range: DateRange | None = None,
        with_metrics: bool = True,
        epic_field: str | None = None,
    ) -> IssueGroup:
        metric_fields = self._get_metric_fields() if with_metrics else {}
        metric_values = {metric_name: [] for metric_name in metric_fields}
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

                issue_metrics: dict[str, int | None] = {}
                for metric_name, field_name in metric_fields.items():
                    value = fields.get(field_name)
                    if value is None:
                        issue_metrics[metric_name] = None
                        continue

                    if not isinstance(value, int):
                        raise ValueError(f"Unexpected Jira field {field_name}: {value}")
                    issue_metrics[metric_name] = value
                    metric_values[metric_name].append(value)

                if isinstance(key, str):
                    epic_link = fields.get(epic_field) if epic_field else None
                    if epic_link is not None and not isinstance(epic_link, str):
                        raise ValueError(f"Unexpected Jira field {epic_field}: {epic_link}")
                    issue_result = Issue(
                        url=self._api_client.issue_url(key),
                        raw=issue,
                        metrics=issue_metrics or None,
                    )
                    self._attach_epic(issue_result, epic_link)
                    self._attach_parent(issue_result, fields.get("parent"))
                    issue_results.append(issue_result)

        return IssueGroup(
            jql=jql,
            user=user,
            date_range=date_range,
            issues=issue_results,
            metrics=metric_values or None,
        )

    def _attach_epic(self, issue: Issue, epic_link: str | None) -> None:
        """Attach an epic URL and resolved summary to a Jira issue."""
        if not epic_link:
            return
        issue.epic_link = epic_link
        issue.epic_url = self._api_client.issue_url(epic_link)
        issue.epic_name = self._get_epic_name(epic_link)

    def _get_epic_name(self, epic_link: str) -> str | None:
        """Return a cached epic issue summary."""
        if epic_link not in self._epic_names:
            self._epic_names[epic_link] = self._api_client.issue(epic_link).summary
        return self._epic_names[epic_link]

    def _attach_parent(self, issue: Issue, parent: object) -> None:
        """Attach a parent issue link and summary to an issue."""
        if parent is None:
            return
        if not isinstance(parent, dict):
            raise ValueError(f"Unexpected Jira field parent: {parent}")
        parent_payload = cast(dict[str, object], parent)

        parent_link = parent_payload.get("key")
        if not isinstance(parent_link, str):
            return

        issue.parent_link = parent_link
        issue.parent_url = self._api_client.issue_url(parent_link)
        parent_fields = parent_payload.get("fields")
        if not isinstance(parent_fields, dict):
            return
        parent_fields_payload = cast(dict[str, object], parent_fields)

        parent_name = parent_fields_payload.get("summary")
        if parent_name is not None and not isinstance(parent_name, str):
            raise ValueError(f"Unexpected Jira parent issue summary: {parent_name}")
        issue.parent_name = parent_name
