from .client import ABCUsersClient
from .resources import User


class MockUsersClient(ABCUsersClient):
    """Resolve users from in-memory test data."""

    def __init__(self, users: dict[str, User] | None = None) -> None:
        """Initialize class instance."""
        self._users = users or {}

    def get_user(self, username: str) -> User:
        """Resolve a Jira user from in-memory test data."""
        user = self._users.get(username)
        if user is not None:
            return user

        return User(username=username)
