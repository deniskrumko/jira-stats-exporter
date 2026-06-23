from enum import StrEnum

from pydantic import BaseModel

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


class IssueStatus(StrEnum):
    """Jira issue status."""

    CLOSED = "closed"


class Issue(BaseModel):
    """Jira issue."""

    url: str
    summary: str | None
    status: IssueStatus

    @property
    def code(self) -> str:
        return self.url.split("/")[-1]


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
