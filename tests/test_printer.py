from app.config import CLIConfig
from app.printer import CLIPrinter
from app.resources import Issue, IssueGroup


def test_issue_group_output_truncates_summary(capsys) -> None:
    """Truncate issue summaries using CLI configuration."""
    printer = CLIPrinter(CLIConfig(max_summary_length=10))
    issue_group = IssueGroup(
        issues=[
            Issue(
                raw={"key": "ML-1", "fields": {"summary": "Very long issue summary"}},
                url="https://jira.example.test/browse/ML-1",
            )
        ]
    )

    printer.print_issue_group(issue_group, show_metrics=False)

    output = capsys.readouterr().out
    assert "ML-1: Very lo..." in output
    assert "Very long issue summary" not in output
