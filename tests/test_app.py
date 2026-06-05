from pathlib import Path

import pytest

from app.app import App
from app.resources import Team


def test_get_team_reads_default_team_config(tmp_path: Path) -> None:
    """Read responsible users from the default configured team."""
    config = _write_config(tmp_path)

    team = _app(config).default_team

    assert isinstance(team, Team)
    assert team.name == "ML & Operations"
    assert team.shortcut == "ml"
    assert team.users == ["krumko", "turdubaev"]


def test_get_team_reads_team_config_by_shortcut(tmp_path: Path) -> None:
    """Read responsible users from a configured team shortcut."""
    config = _write_config(tmp_path)

    team = _app(config).get_team("ops")

    assert team.users == ["sitko"]


def test_get_team_does_not_read_team_config_by_name(tmp_path: Path) -> None:
    """Reject team name lookups."""
    config = _write_config(tmp_path)

    with pytest.raises(ValueError, match="Team was not found"):
        _app(config).get_team("Operations")


def test_get_team_fails_for_missing_default_team(tmp_path: Path) -> None:
    """Fail when no default team is configured."""
    config = tmp_path / "config.toml"
    config.write_text(
        """
[[teams]]
name = "Operations"
shortcut = "ops"
users = ["sitko"]
""".strip()
    )

    with pytest.raises(ValueError, match="Default team is not configured"):
        _app(config).get_team()


def test_get_team_fails_for_unknown_team(tmp_path: Path) -> None:
    """Fail when requested team is not configured."""
    config = _write_config(tmp_path)

    with pytest.raises(ValueError, match="Team was not found"):
        _app(config).get_team("unknown")


def test_get_team_reuses_loaded_config(tmp_path: Path) -> None:
    """Reuse application config loaded during initialization."""
    config = _write_config(tmp_path)
    app = _app(config)
    config.unlink()

    assert app.get_team("ops").users == ["sitko"]


def test_teams_are_indexed_by_shortcut(tmp_path: Path) -> None:
    """Index teams by shortcut during initialization."""
    config = _write_config(tmp_path)

    app = _app(config)

    assert set(app.teams) == {"ml", "ops"}
    assert app.teams["ml"].name == "ML & Operations"


def _app(config_path: Path) -> App:
    """Build an application without real Jira clients."""
    return App(
        client=object(),
        custom_fields_client=object(),
        jql_client=object(),
        config=config_path,
    )


def _write_config(tmp_path: Path) -> Path:
    """Write a test application config."""
    config = tmp_path / "config.toml"
    config.write_text(
        """
[cli]
max_summary_length = 60

[[teams]]
name = "ML & Operations"
shortcut = "ml"
default = true
users = ["krumko", "turdubaev"]

[[teams]]
name = "Operations"
shortcut = "ops"
users = ["sitko"]
""".strip()
    )
    return config
