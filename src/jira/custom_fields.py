import json
from pathlib import Path
from typing import Any, overload

from jira.client import JiraAPIClient


class JiraCustomFieldsClient:
    """Load Jira custom field names and replace custom field IDs in payloads."""

    def __init__(
        self,
        api: JiraAPIClient | None = None,
        cache_path: Path = Path("/tmp/jira_stats_exporter") / "custom_fields.json",
        custom_fields: dict[str, str] | None = None,
    ) -> None:
        """Initialize class instance."""
        self._api = api
        self._cache_path = cache_path

        self._custom_fields: dict[str, str] | None = custom_fields
        self._name_to_custom_field: dict[str, str] | None = None

    def get_fields(self) -> dict[str, str]:
        """Return cached or freshly fetched Jira custom field ID-to-name mappings."""
        # Use inner cache
        if self._custom_fields is not None:
            return self._custom_fields

        # Use file cache
        if self._cache_path.exists():
            with self._cache_path.open(encoding="utf-8") as file:
                payload = json.load(file)
            if not isinstance(payload, dict):
                raise RuntimeError(f"Unexpected cache format: {self._cache_path}")
            self._custom_fields = {str(key): str(value) for key, value in payload.items()}
            return self._custom_fields

        # Use API to fetch fields
        fields = self._fetch_fields_from_api()
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_path.open("w", encoding="utf-8") as file:
            json.dump(fields, file, indent=2, ensure_ascii=False, sort_keys=True)
            file.write("\n")

        self._custom_fields = fields
        return fields

    def get_field_by_name(self, field_name: str) -> str:
        """Return a custom field ID by name or the original field name."""
        if self._name_to_custom_field is None:
            self._name_to_custom_field = {
                mapped_field_name: field_id
                for field_id, mapped_field_name in self.get_fields().items()
            }

        return self._name_to_custom_field.get(field_name, field_name)

    def replace(
        self,
        payload: dict,
        fields: dict[str, str] | None = None,
    ) -> dict:
        """Replace custom field IDs in a Jira payload with human-readable names."""
        custom_fields = fields if fields is not None else self.get_fields()
        return self._replace_custom_field_keys(payload, custom_fields)

    def _fetch_fields_from_api(self) -> dict[str, str]:
        """Fetch Jira custom field mappings from Jira field metadata."""
        if self._api is None:
            raise RuntimeError("Jira API client not initialized")

        fields: dict[str, str] = {}
        for field in self._api.fields():
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

    @overload
    def _replace_custom_field_keys(
        self,
        payload: dict,
        fields: dict[str, str],
    ) -> dict: ...

    @overload
    def _replace_custom_field_keys(
        self,
        payload: list,
        fields: dict[str, str],
    ) -> list: ...

    def _replace_custom_field_keys(
        self,
        payload: list | dict | str,
        fields: dict[str, str],
    ) -> list | dict | str:
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
