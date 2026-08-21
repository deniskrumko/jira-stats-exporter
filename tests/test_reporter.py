from datetime import date
from pathlib import Path

from app.app import App
from app.resources import TIME_METRICS, Issue, IssueGroup
from core.date_ranges import DateRange
from jira import JQLClient, MockJiraAPIClient, MockJiraCustomFieldsClient
from reporter import HTMLReporter, MockReporterClient, UserReport
from reporter.markup import render_jira_markup
from teams import MockTeamsClient
from users import MockUsersClient, User


def test_app_returns_complete_report_data() -> None:
    """Load all report categories and attach metrics to every issue."""
    api_client = MockJiraAPIClient()
    app = App(
        api_client=api_client,
        cf_client=MockJiraCustomFieldsClient(),
        jql_client=JQLClient(),
        users_client=MockUsersClient({"me": User(username="krumko")}),
        teams_client=MockTeamsClient({}),
    )
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 31))

    progress_messages: list[str] = []
    report = app.get_report_data("me", date_range, progress_messages.append)

    assert report.user.username == "krumko"
    assert len(api_client.search_calls) == 3
    assert "resolution changed during" in api_client.search_calls[0]["jql"]
    assert "status in" in api_client.search_calls[1]["jql"]
    assert 'created >= "2026-05-01"' in api_client.search_calls[2]["jql"]
    expected_fields = [
        "key",
        "summary",
        "description",
        "status",
        "labels",
        "customfield_12606",
        "customfield_12602",
        "customfield_12603",
        "customfield_12604",
        "customfield_12605",
    ]
    assert all(call["fields"] == expected_fields for call in api_client.search_calls)
    assert report.closed.issues[0].metrics == {
        "TTM": 3600,
        "Time in Progress": 1200,
        "Time in Review": 600,
        "Time in Resolved": 300,
    }
    assert report.closed.issues[0].epic_name == "Platform epic"
    assert report.closed.issues[0].epic_link == "ML-2161"
    assert report.closed.issues[0].epic_url == "https://jira.example.test/browse/ML-2161"
    assert report.closed.issues[0].labels == ["backend", "priority"]
    assert api_client.issue_calls == ["ML-2161"]
    assert report.created.date_range == date_range
    assert report.in_progress.date_range is None
    assert progress_messages == [
        "krumko: Loading closed issues",
        "krumko: Loading in-progress issues",
        "krumko: Loading created issues",
    ]


def test_html_reporter_writes_safe_complete_report(tmp_path: Path) -> None:
    """Write complete escaped HTML with readable issue metrics."""
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 7))
    issue = Issue(
        raw={
            "key": "ML-1",
            "fields": {
                "summary": "Fix <script>alert(1)</script>",
                "description": (
                    "Read https://example.com/docs?q=one&lang=ru.\n"
                    "Mirror www.example.org/path\n"
                    "!attachment.png|thumbnail!"
                ),
                "status": {"name": "In progress"},
                "labels": ["backend", "needs <review>"],
            },
        },
        url="https://jira.example.test/browse/ML-1?source=a&view=b",
        metrics={
            "TTM": 90061,
            "Time in Progress": 3600,
            "Time in Review": None,
            "Time in Resolved": 0,
        },
        epic_link="ML-2161",
        epic_url="https://jira.example.test/browse/ML-2161",
        epic_name="Platform epic",
    )
    group = IssueGroup(issues=[issue], user=User(username="krumko"))
    empty_group = IssueGroup(issues=[], user=User(username="krumko"))
    user_report = UserReport(
        user=User(username="krumko"),
        closed=group,
        in_progress=empty_group,
        created=group,
    )
    progress_messages: list[str] = []
    reporter = HTMLReporter(
        lambda _user, _date_range, _progress: user_report,
        output_dir=tmp_path,
    )

    path = reporter.create_report(["me"], date_range, progress_messages.append)

    assert path.parent == tmp_path
    assert path.name.startswith("jira_report_")
    assert path.suffix == ".html"
    html = path.read_text(encoding="utf-8")
    assert "2026-05-01 — 2026-05-07" in html
    assert 'Tasks in status "Closed" (1)' in html
    assert 'Tasks in status "In progress" (0)' in html
    assert 'Tasks in status "Created" (1)' in html
    assert "Fix &lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "User krumko" in html
    assert 'target="_blank" rel="noopener noreferrer">ML-1</a>' in html
    assert 'href="https://example.com/docs?q=one&amp;lang=ru" target="_blank"' in html
    assert 'href="https://www.example.org/path" target="_blank"' in html
    assert "📎 attachment.png" in html
    assert 'class="attachment"' in html
    assert "thumbnail!" not in html
    assert ">Platform epic</a>" in html
    assert 'href="https://jira.example.test/browse/ML-2161" target="_blank"' in html
    assert '<span class="label">backend</span>' in html
    assert '<span class="label">needs &lt;review&gt;</span>' in html
    assert "source=a&amp;view=b" in html
    assert "1d 1h 1m" in html
    assert "No issues</p>" in html
    assert "No issues.</p>" not in html
    assert all(metric in html for metric in TIME_METRICS)
    assert "Content-Security-Policy" in html
    assert "script-src 'none'" in html
    assert progress_messages == [
        "Collecting data for me (1/1)",
        "Rendering HTML",
        "Saving report",
    ]


def test_html_reporter_shows_missing_labels(tmp_path: Path) -> None:
    """Show a red missing-labels badge beside issue status."""
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 7))
    issue = Issue(raw={"key": "ML-1", "fields": {"labels": []}})
    group = IssueGroup(issues=[issue])
    report = UserReport(
        user=User(username="krumko"),
        closed=group,
        in_progress=IssueGroup(issues=[]),
        created=IssueGroup(issues=[]),
    )
    reporter = HTMLReporter(
        lambda _user, _date_range, _progress: report,
        output_dir=tmp_path,
    )

    html = reporter.create_report(["me"], date_range).read_text(encoding="utf-8")

    assert '<span class="no-labels">No labels</span>' in html


def test_jira_markup_renders_rich_description() -> None:
    """Render Jira headings, effects, lists, tables, code, and attachments."""
    description = """*Контекст*

Ранее оказалось {*}недостаточно{*}.

*Что нужно сделать*
# *Проверить и почистить данные*
** Склеить файл ({{{}Ver_result_kolesa.xlsx{}}})
** Проверить даты
# *Оценить качество*
** Посчитать статистическую связь

||Признак||Качество||
|score|высокое|

{noformat}
raw *text*
{noformat}

[^Анализ.ipynb]
!chart.png|thumbnail!

h3. *{color:#FF0000}Выводы{color}*
"""

    html = render_jira_markup(
        description,
        "https://jira.example.test/browse/ML-1?source=report&view=full",
    )

    assert "<strong>Контекст</strong>" in html
    assert "<strong>недостаточно</strong>" in html
    assert "<ol>" in html
    assert "<ul>" in html
    assert "<li>Склеить файл" in html
    assert "<code>Ver_result_kolesa.xlsx</code>" in html
    assert "<table>" in html
    assert "<pre><code>raw *text*" in html
    assert '<h3><strong><font color="#FF0000">Выводы</font></strong></h3>' in html
    assert "📎 Анализ.ipynb" in html
    assert "📎 chart.png" in html
    assert html.count('class="attachment"') == 2
    assert 'href="https://jira.example.test/browse/ML-1?source=report&amp;view=full"' in html
    assert "<img" not in html


def test_jira_markup_sanitizes_xss_payloads() -> None:
    """Remove executable HTML, dangerous attributes, and unsafe URL schemes."""
    description = """Safe text
<script>alert(1)</script>
<style>body { display: none }</style>
<iframe src="https://evil.example"></iframe>
<img src="x" onerror="alert(2)">
<a href="javascript:alert(3)" onclick="alert(4)">bad link</a>
<a href="data:text/html,evil">data link</a>
<a href="https://safe.example" title="Safe" onclick="alert(5)">safe link</a>
"""

    html = render_jira_markup(description)

    assert "Safe text" in html
    assert "alert(" not in html
    assert "display: none" not in html
    assert "<script" not in html
    assert "<style" not in html
    assert "<iframe" not in html
    assert "<img" not in html
    assert "javascript:" not in html
    assert "data:text" not in html
    assert "onclick" not in html
    assert '<a target="_blank" rel="noopener noreferrer">bad link</a>' in html
    assert 'href="https://safe.example"' in html
    assert 'target="_blank" rel="noopener noreferrer"' in html


def test_mock_reporter_records_calls(tmp_path: Path) -> None:
    """Record mock report users and date range."""
    path = tmp_path / "report.html"
    reporter = MockReporterClient(path)
    date_range = DateRange(start=date(2026, 5, 1), end=date(2026, 5, 7))

    result = reporter.create_report(["krumko", "pupa"], date_range)

    assert result == path
    assert reporter.calls == [(["krumko", "pupa"], date_range)]
