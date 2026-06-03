from datetime import date

from core.date_ranges import DateRange
from jira.jql import JQLClient


def test_closed_issues_builds_jql() -> None:
    """Build JQL for closed issues."""
    jql = JQLClient().closed_issues(
        "krumko",
        DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31)),
    )

    assert jql == (
        "Responsibles in (krumko)\n"
        'AND status changed to (Closed, "Deployed to production", "On Approval", '
        'Introduction, "Ready for Deploy", "Beta Testing")\n'
        'AND resolution changed during ("2026-05-01", "2026-05-31") '
        "to (Fixed, Done, Resolved)"
    )


def test_closed_issues_quotes_responsible_when_needed() -> None:
    """Quote responsible values with non-identifier characters."""
    jql = JQLClient().closed_issues(
        "john smith",
        DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31)),
    )

    assert jql.startswith('Responsibles in ("john smith")')
