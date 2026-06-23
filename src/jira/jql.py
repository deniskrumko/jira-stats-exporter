from core.date_ranges import DateRange
from users import User

DONE_RESOLUTIONS = ("Fixed", "Done", "Resolved")
DONE_STATUSES = (
    "Closed",
    "Deployed to production",
    "On Approval",
    "Introduction",
    "Ready for Deploy",
    "Beta Testing",
)
IN_PROGRESS_STATUSES = (
    "In progress",
    "Research",
)


class JQLClient:
    """Build JQL queries for Jira searches."""

    def closed_issues(self, user: User, date_range: DateRange) -> str:
        """Build JQL for closed issues within an inclusive date range."""
        statuses = ", ".join(self._quote_value(status) for status in DONE_STATUSES)
        resolutions = ", ".join(self._quote_value(resolution) for resolution in DONE_RESOLUTIONS)
        return (
            f"Responsibles in ({self._quote_value(user.username)})\n"
            f"AND status changed to ({statuses})\n"
            "AND resolution changed during "
            f'("{date_range.start.isoformat()}", "{date_range.end.isoformat()}") '
            f"to ({resolutions})"
        )

    def in_progress_issues(self, user: User) -> str:
        """Build JQL for closed issues within an inclusive date range."""
        statuses = ", ".join(self._quote_value(status) for status in IN_PROGRESS_STATUSES)
        return f"assignee in ({self._quote_value(user.username)}) AND status in ({statuses})\n"

    def _quote_value(self, value: str) -> str:
        """Quote a JQL value when it contains non-identifier characters."""
        if value.replace("_", "").replace("-", "").isalnum():
            return value
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
