from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.resources import TIME_METRICS
from core.date_ranges import DateRange

from .markup import render_jira_markup
from .resources import UserReport

type ReportProgress = Callable[[str], None]
type ReportDataLoader = Callable[[str, DateRange, ReportProgress | None], UserReport]

COMPONENTS_DIR = Path(__file__).parent / "components"


def _create_template_environment() -> Environment:
    """Create the HTML component template environment."""
    return Environment(
        loader=FileSystemLoader(COMPONENTS_DIR),
        autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


class ABCReporterClient(ABC):
    """Define the report generation client interface."""

    @abstractmethod
    def create_report(
        self,
        users: list[str],
        date_range: DateRange,
        progress: ReportProgress | None = None,
    ) -> Path:
        """Create a report for Jira users and a date range."""


class HTMLReporter(ABCReporterClient):
    """Generate self-contained HTML reports from Jira issue data."""

    def __init__(
        self,
        data_loader: ReportDataLoader,
        output_dir: Path = Path("/tmp/jira_stats_exporter/reports"),
    ) -> None:
        """Initialize class instance."""
        self._data_loader = data_loader
        self._output_dir = output_dir
        self._template = _create_template_environment().get_template("report.html")

    def create_report(
        self,
        users: list[str],
        date_range: DateRange,
        progress: ReportProgress | None = None,
    ) -> Path:
        """Create an HTML report for Jira users and a date range."""
        created_at = datetime.now().astimezone()
        reports = []
        for index, user in enumerate(users, start=1):
            self._notify(progress, f"Collecting data for {user} ({index}/{len(users)})")
            reports.append(self._data_loader(user, date_range, progress))

        self._notify(progress, "Rendering HTML")
        html = self._render(reports, date_range, created_at)
        self._notify(progress, "Saving report")
        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self._output_dir / f"jira_report_{created_at:%Y%m%d_%H%M%S_%f}.html"
        path.write_text(html, encoding="utf-8")
        return path

    @staticmethod
    def _notify(progress: ReportProgress | None, message: str) -> None:
        """Send a report progress message when a callback is configured."""
        if progress is not None:
            progress(message)

    def _render(
        self,
        reports: list[UserReport],
        date_range: DateRange,
        created_at: datetime,
    ) -> str:
        """Render a complete HTML report document."""
        return self._template.render(
            reports=reports,
            date_range=date_range,
            created_at=created_at,
            time_metrics=TIME_METRICS,
            format_duration=self._format_duration,
            render_jira_markup=render_jira_markup,
        )

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds as days, hours, and minutes."""
        days, remainder = divmod(seconds, 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes = remainder // 60
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes or not parts:
            parts.append(f"{minutes}m")
        return " ".join(parts)
