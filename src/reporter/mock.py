from pathlib import Path

from core.date_ranges import DateRange

from .client import ABCReporterClient, ReportProgress


class MockReporterClient(ABCReporterClient):
    """Record report requests without generating report files."""

    def __init__(self, report_path: Path = Path("/tmp/jira_report_mock.html")) -> None:
        """Initialize class instance."""
        self.report_path = report_path
        self.calls: list[tuple[list[str], DateRange]] = []

    def create_report(
        self,
        users: list[str],
        date_range: DateRange,
        progress: ReportProgress | None = None,
    ) -> Path:
        """Record a report request and return the configured path."""
        self.calls.append((users, date_range))
        if progress is not None:
            progress("Generating report")
        return self.report_path
