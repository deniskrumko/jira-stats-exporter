from pydantic import BaseModel, ConfigDict

from core.date_ranges import DateRange


class ClosedIssue(BaseModel):
    """Represent a closed issue link and title."""

    model_config = ConfigDict(frozen=True)

    url: str
    summary: str | None


class ClosedIssuesStats(BaseModel):
    """Represent closed issue links and aggregate timing stats."""

    model_config = ConfigDict(frozen=True)

    responsible: str
    date_range: DateRange
    issues: list[ClosedIssue]
    avg_time_seconds: dict[str, int]

    @property
    def closed_issues_per_week(self) -> float | None:
        """Return closed issues per week for ranges longer than one week."""
        days = (self.date_range.end - self.date_range.start).days + 1
        if days <= 7:
            return None
        return len(self.issues) / (days / 7)
