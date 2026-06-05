def test_get_field_by_name_returns_custom_field_id(jira_cf_client) -> None:
    """Return a custom field ID by field name."""
    assert jira_cf_client.get_field_by_name("TTM") == "customfield_12602"


def test_get_field_by_name_returns_original_name_when_not_custom(jira_cf_client) -> None:
    """Return the original field name when no custom field exists."""
    assert jira_cf_client.get_field_by_name("test") == "test"
