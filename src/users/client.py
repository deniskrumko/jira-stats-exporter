from abc import ABC, abstractmethod
from typing import Protocol

from .resources import CURRENT_USER_ALIAS, User, UsersConfig


class JiraMeClient(Protocol):
    """Jira client capable of returning the current user."""

    def me(self) -> dict[str, object]:
        """Fetch information about the authenticated Jira user."""
        ...


class ABCUsersClient(ABC):
    """Abstract base class for resolving Jira users."""

    @abstractmethod
    def get_user(self, username: str) -> User:
        """Resolve a Jira user."""


class UsersClient(ABCUsersClient):
    """Resolve configured user names for Jira commands."""

    def __init__(self, api_client: JiraMeClient, config: UsersConfig | None = None) -> None:
        """Initialize class instance."""
        self._api_client = api_client
        self._config = config or UsersConfig()

    def get_user(self, username: str) -> User:
        """Resolve a configured alias or the current Jira user."""
        username = self._resolve_alias(username)
        username = self._resolve_me(username)
        return User(username=username, aliases=self._get_aliases(username))

    def _resolve_alias(self, username: str) -> str:
        """Resolve configured user alias."""
        return self._config.aliases.get(username, username)

    def _resolve_me(self, username: str) -> str:
        """Resolve current Jira user name."""
        if username != CURRENT_USER_ALIAS:
            return username

        name = self._api_client.me().get("name")
        if not name or not isinstance(name, str):
            raise RuntimeError("Unable to resolve current Jira user")

        return name

    def _get_aliases(self, username: str) -> list[str] | None:
        """Find configured aliases for user name."""
        aliases = [
            alias
            for alias, alias_username in self._config.aliases.items()
            if alias_username == username
        ]
        return aliases or None
