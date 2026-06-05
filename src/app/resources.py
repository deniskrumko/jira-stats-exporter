from enum import StrEnum
from typing import Iterator

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


class Team(BaseModel):
    """Jira team."""

    name: str
    shortcut: str
    users: list[str]
    default: bool = False


class Issue(BaseModel):
    """Jira issue."""

    url: str
    summary: str | None
    status: IssueStatus

    @property
    def code(self) -> str:
        return self.url.split("/")[-1]


class Issues(BaseModel):
    """Jira issues and aggregate timing stats."""

    responsible: str
    date_range: DateRange
    issues: list[Issue]
    avg_time_in_status: dict[str, int]

    def __iter__(self) -> Iterator[Issue]:  # ty: ignore[invalid-method-override]
        """Iterate over issues."""
        return iter(self.issues)

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
