from abc import ABC, abstractmethod
from functools import cached_property

from .resources import Team


class ABCTeamsClient(ABC):
    """Resolve Jira teams from command input."""

    @abstractmethod
    def get_team(self, shortcut: str | None = None) -> Team:
        """Get team by shortcut name."""

    @property
    @abstractmethod
    def default_team(self) -> Team:
        """Return configured default team."""


class TeamsClient(ABCTeamsClient):
    """Resolve configured Jira teams."""

    def __init__(self, teams: dict[str, Team]) -> None:
        """Initialize class instance."""
        self._teams = teams

    def get_team(self, shortcut: str | None = None) -> Team:
        """Get team by shortcut name."""
        if shortcut is None:
            return self.default_team

        team = self._teams.get(shortcut)
        if team is None:
            raise ValueError(f"Team was not found by shortcut: {shortcut}")

        return team

    @property
    def default_team(self) -> Team:
        """Return configured default team."""
        return self._default_team

    @cached_property
    def _default_team(self) -> Team:
        """Return cached configured default team."""
        for team in self._teams.values():
            if team.default:
                return team

        raise ValueError("Default team is not configured")
