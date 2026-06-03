import json
from pathlib import Path
from typing import Any

from jira import JiraAPIClient


class JiraCustomFieldsClient:
    """Load Jira custom field names and replace custom field IDs in payloads."""

    def __init__(
        self,
        client: JiraAPIClient | None = None,
        cache_path: Path = Path(".cache") / "custom_fields.json",
    ) -> None:
        """Initialize class instance."""
        self._client = client or JiraAPIClient()
        self._cache_path = cache_path
        self._fields: dict[str, str] | None = None

    def get_fields(self) -> dict[str, str]:
        """Return cached or freshly fetched Jira custom field ID-to-name mappings."""
        if self._fields is not None:
            return self._fields

        if self._cache_path.exists():
            with self._cache_path.open(encoding="utf-8") as file:
                payload = json.load(file)
            if not isinstance(payload, dict):
                raise RuntimeError(f"Unexpected cache format: {self._cache_path}")
            self._fields = {str(key): str(value) for key, value in payload.items()}
            return self._fields

        fields = self._fetch_fields()
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_path.open("w", encoding="utf-8") as file:
            json.dump(fields, file, indent=2, ensure_ascii=False, sort_keys=True)
            file.write("\n")
        self._fields = fields
        return fields

    def replace(
        self,
        payload: dict[str, Any],
        fields: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Replace custom field IDs in a Jira payload with human-readable names."""
        custom_fields = fields if fields is not None else self.get_fields()
        return self._replace_custom_field_keys(payload, custom_fields)

    def _fetch_fields(self) -> dict[str, str]:
        """Fetch Jira custom field mappings from Jira field metadata."""
        fields: dict[str, str] = {}
        for field in self._client.fields():
            if not isinstance(field, dict):
                continue

            field_id = field.get("id")
            field_name = field.get("name")
            if (
                isinstance(field_id, str)
                and field_id.startswith("customfield_")
                and isinstance(field_name, str)
            ):
                fields[field_id] = field_name

        return fields

    def _replace_custom_field_keys(
        self,
        payload: Any,
        fields: dict[str, str],
    ) -> Any:
        """Recursively replace Jira custom field keys inside a payload."""
        if isinstance(payload, dict):
            replaced: dict[str, Any] = {}
            for key, value in payload.items():
                original_key = str(key)
                replaced_key = fields.get(original_key, original_key)
                if replaced_key in replaced:
                    replaced_key = f"{replaced_key} ({original_key})"
                replaced[replaced_key] = self._replace_custom_field_keys(value, fields)
            return replaced

        if isinstance(payload, list):
            return [self._replace_custom_field_keys(item, fields) for item in payload]

        return payload
