from pydantic import BaseModel, Field

CURRENT_USER_ALIAS = "me"


class User(BaseModel):
    """Jira user resolved from command input."""

    username: str
    aliases: list[str] | None = None


class UsersConfig(BaseModel):
    """Configure user aliases for Jira commands."""

    aliases: dict[str, str] = Field(default_factory=dict)
