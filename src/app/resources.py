from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from core.date_ranges import DateRange
from core.utils import avg
from users import User

DEFAULT_TEAM_MARKER = "__default__"

TIME_METRICS = (
    "TTM",
    "Time in Progress",
    "Time in Review",
    "Time in Resolved",
)


class CLICommands(StrEnum):
    ME = "me"
    ISSUE = "issue"
    CLOSED = "closed"
    IN_PROGRESS = "inprogress"


class Issue(BaseModel):
    """Jira issue."""

    raw: dict[str, Any] = Field(default_factory=dict)
    url: str | None = None

    @property
    def code(self) -> str:
        """Return Jira issue key."""
        key = self.raw.get("key")
        if isinstance(key, str):
            return key

        if self.url:
            return self.url.split("/")[-1]

        return ""

    @property
    def assignee(self) -> str | None:
        """Return Jira issue assignee username."""
        fields = self._fields
        assignee = fields.get("assignee")
        if not isinstance(assignee, dict):
            return None

        name = assignee.get("name")
        return name if isinstance(name, str) else None

    @property
    def description(self) -> str | None:
        """Return Jira issue description."""
        description = self._fields.get("description")
        return description if isinstance(description, str) else None

    @property
    def status(self) -> str | None:
        """Return Jira issue status name."""
        status = self._fields.get("status")
        if not isinstance(status, dict):
            return None

        name = status.get("name")
        return name if isinstance(name, str) else None

    @property
    def summary(self) -> str | None:
        """Return Jira issue summary."""
        summary = self._fields.get("summary")
        return summary if isinstance(summary, str) else None

    @property
    def title(self) -> str | None:
        """Return Jira issue title."""
        return self.summary

    @property
    def _fields(self) -> dict[str, Any]:
        """Return raw Jira issue fields."""
        fields = self.raw.get("fields")
        return fields if isinstance(fields, dict) else {}


class IssueGroup(BaseModel):
    """Jira issues and aggregate timing stats."""

    issues: list[Issue]
    user: User | None = None
    date_range: DateRange | None = None
    metrics: dict[str, list[int]] | None = None

    @property
    def issues_per_week(self) -> float | None:
        """Return issues per week for ranges longer than one week."""
        if self.date_range is None:
            raise ValueError("Can't get issues_per_week without date range")

        days = (self.date_range.end - self.date_range.start).days + 1
        if days <= 7:
            return None
        return len(self.issues) / (days / 7)

    @property
    def count(self) -> int:
        """Return the number of issues."""
        return len(self.issues)

    @property
    def total_ttm(self) -> int:
        """Return the total time to resolve all issues."""
        if self.avg_time_in_status is None:
            raise ValueError("Can't get total ttm")

        return sum(self.avg_time_in_status["TTM"] for issue in self.issues)

    @property
    def avg_time_in_status(self) -> dict[str, int]:
        if not self.metrics:
            raise ValueError("No metrics")

        return {metric_name: avg(values) for metric_name, values in self.metrics.items()}
