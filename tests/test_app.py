import pytest

from teams import Team


def test_get_team_reads_default_team_config(app) -> None:
    """Read responsible users from the default configured team."""
    team = app.default_team

    assert isinstance(team, Team)
    assert team.name == "Pupa And Lupa Group"
    assert team.users == ["pupa", "lupa"]


def test_get_team_reads_team_config_by_shortcut(app) -> None:
    """Read responsible users from a configured team shortcut."""
    assert app.get_team("kr").users == ["krumko"]


def test_get_team_does_not_read_team_config_by_name(app) -> None:
    """Reject team name lookups."""
    with pytest.raises(ValueError, match="Team was not found"):
        app.get_team("Operations")


def test_get_team_fails_for_unknown_team(app) -> None:
    """Fail when requested team is not configured."""
    with pytest.raises(ValueError, match="Team was not found"):
        app.get_team("unknown")
