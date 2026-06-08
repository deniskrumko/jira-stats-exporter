from users import MockUsersClient, User, UsersClient, UsersConfig


class FakeJiraAPIClient:
    """Provide Jira client responses for user tests."""

    def me(self) -> dict[str, str]:
        """Return fake current user data."""
        return {"name": "krumko"}


def test_get_user_resolves_configured_alias() -> None:
    """Return a user resolved from configured aliases."""
    client = UsersClient(
        FakeJiraAPIClient(),
        UsersConfig(aliases={"arstan": "turdubaev"}),
    )

    user = client.get_user("arstan")

    assert user.username == "turdubaev"
    assert user.aliases == ["arstan"]


def test_get_user_resolves_me() -> None:
    """Return the current Jira user for me."""
    client = UsersClient(FakeJiraAPIClient())

    user = client.get_user("me")

    assert user.username == "krumko"
    assert user.aliases is None


def test_mock_get_user_resolves_configured_user() -> None:
    """Return a configured mock user."""
    client = MockUsersClient({"arstan": User(username="turdubaev", aliases=["arstan"])})

    user = client.get_user("arstan")

    assert user.username == "turdubaev"
    assert user.aliases == ["arstan"]


def test_mock_get_user_returns_username_by_default() -> None:
    """Return input username when no mock user is configured."""
    client = MockUsersClient()

    user = client.get_user("arstan")

    assert user.username == "arstan"
    assert user.aliases is None
