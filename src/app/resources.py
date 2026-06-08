from enum import StrEnum

from pydantic import BaseModel

from core.date_ranges import DateRange

TIME_METRICS = (
    "TTM",
    "Time in Progress",
    "Time in Review",
    "Time in Resolved",
)


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

    responsible: str
    date_range: DateRange
    issues: list[Issue]
    avg_time_in_status: dict[str, int]

    @property
    def issues_per_week(self) -> float | None:
        """Return issues per week for ranges longer than one week."""
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
        return sum(self.avg_time_in_status["TTM"] for issue in self.issues)
