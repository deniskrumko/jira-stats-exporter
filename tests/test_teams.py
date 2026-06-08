import pytest

from teams import MockTeamsClient, Team, TeamsClient


def test_get_team_reads_default_team() -> None:
    """Read the configured default team."""
    client = TeamsClient(
        {
            "pl": Team(name="Pupa And Lupa Group", users=["pupa", "lupa"], default=True),
            "kr": Team(name="Krumko Productions", users=["krumko"]),
        }
    )

    assert client.default_team.name == "Pupa And Lupa Group"


def test_get_team_reads_team_by_shortcut() -> None:
    """Read a configured team by shortcut."""
    client = TeamsClient(
        {
            "pl": Team(name="Pupa And Lupa Group", users=["pupa", "lupa"], default=True),
            "kr": Team(name="Krumko Productions", users=["krumko"]),
        }
    )

    assert client.get_team("kr").users == ["krumko"]


def test_get_team_fails_for_unknown_shortcut() -> None:
    """Fail when requested team shortcut is not configured."""
    client = TeamsClient(
        {
            "pl": Team(name="Pupa And Lupa Group", users=["pupa", "lupa"], default=True),
        }
    )

    with pytest.raises(ValueError, match="Team was not found"):
        client.get_team("unknown")


def test_mock_get_team_reads_configured_team() -> None:
    """Read a configured mock team by shortcut."""
    client = MockTeamsClient(
        {
            "pl": Team(name="Pupa And Lupa Group", users=["pupa", "lupa"], default=True),
        }
    )

    assert client.get_team("pl").users == ["pupa", "lupa"]
