from core.date_ranges import DateRange

DONE_RESOLUTIONS = ("Fixed", "Done", "Resolved")
DONE_STATUSES = (
    "Closed",
    "Deployed to production",
    "On Approval",
    "Introduction",
    "Ready for Deploy",
    "Beta Testing",
)


class JQLClient:
    """Build JQL queries for Jira searches."""

    def closed_issues(self, responsible: str, date_range: DateRange) -> str:
        """Build JQL for closed issues within an inclusive date range."""
        statuses = ", ".join(self._quote_value(status) for status in DONE_STATUSES)
        resolutions = ", ".join(self._quote_value(resolution) for resolution in DONE_RESOLUTIONS)
        return (
            f"Responsibles in ({self._quote_value(responsible)})\n"
            f"AND status changed to ({statuses})\n"
            "AND resolution changed during "
            f'("{date_range.start.isoformat()}", "{date_range.end.isoformat()}") '
            f"to ({resolutions})"
        )

    def _quote_value(self, value: str) -> str:
        """Quote a JQL value when it contains non-identifier characters."""
        if value.replace("_", "").replace("-", "").isalnum():
            return value
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
