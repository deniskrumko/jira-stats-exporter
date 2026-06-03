from pathlib import Path
from typing import Any

from jira import JiraCustomFieldsClient


class FakeJiraClient:
    """Provide Jira field metadata for custom field tests."""

    def fields(self) -> list[Any]:
        """Return fake Jira fields."""
        return [
            {"id": "customfield_12602", "name": "TTM"},
            {"id": "summary", "name": "Summary"},
        ]


def test_get_field_by_name_returns_custom_field_id(tmp_path: Path) -> None:
    """Return a custom field ID by field name."""
    client = JiraCustomFieldsClient(
        client=FakeJiraClient(),
        cache_path=tmp_path / "custom_fields.json",
    )

    assert client.get_field_by_name("TTM") == "customfield_12602"


def test_get_field_by_name_returns_original_name_when_not_custom(tmp_path: Path) -> None:
    """Return the original field name when no custom field exists."""
    client = JiraCustomFieldsClient(
        client=FakeJiraClient(),
        cache_path=tmp_path / "custom_fields.json",
    )

    assert client.get_field_by_name("summary") == "summary"
