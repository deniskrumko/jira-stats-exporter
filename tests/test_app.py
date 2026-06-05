from pathlib import Path

import pytest

from app.app import JiraStatsExporter


def test_get_team_reads_default_team_config(tmp_path: Path) -> None:
    """Read responsible users from the default configured team."""
    config = _write_config(tmp_path)

    team = _app().get_team(config_path=config)

    assert team.name == "ML & Operations"
    assert team.users == ["krumko", "turdubaev"]


def test_get_team_reads_team_config_by_shortcut(tmp_path: Path) -> None:
    """Read responsible users from a configured team shortcut."""
    config = _write_config(tmp_path)

    team = _app().get_team("ops", config)

    assert team.users == ["sitko"]


def test_get_team_reads_team_config_by_name(tmp_path: Path) -> None:
    """Read responsible users from a configured team name."""
    config = _write_config(tmp_path)

    team = _app().get_team("Operations", config)

    assert team.users == ["sitko"]


def test_get_team_fails_for_missing_default_team(tmp_path: Path) -> None:
    """Fail when no default team is configured."""
    config = tmp_path / "config.toml"
    config.write_text(
        """
[[team]]
name = "Operations"
shortcut = "ops"
users = ["sitko"]
""".strip()
    )

    with pytest.raises(ValueError, match="Default team is not configured"):
        _app().get_team(config_path=config)


def test_get_team_fails_for_unknown_team(tmp_path: Path) -> None:
    """Fail when requested team is not configured."""
    config = _write_config(tmp_path)

    with pytest.raises(ValueError, match="Team is not configured: unknown"):
        _app().get_team("unknown", config)


def _app() -> JiraStatsExporter:
    """Build an application without real Jira clients."""
    return JiraStatsExporter(client=object(), custom_fields_client=object(), jql_client=object())


def _write_config(tmp_path: Path) -> Path:
    """Write a test application config."""
    config = tmp_path / "config.toml"
    config.write_text(
        """
[[team]]
name = "ML & Operations"
shortcut = "ml"
default = true
users = ["krumko", "turdubaev"]

[[team]]
name = "Operations"
shortcut = "ops"
users = ["sitko"]
""".strip()
    )
    return config
