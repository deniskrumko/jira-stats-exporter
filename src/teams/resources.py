from pydantic import BaseModel, model_validator


class Team(BaseModel):
    """Jira team."""

    name: str
    users: list[str]
    default: bool = False

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_users(self) -> "Team":
        """Validate configured team users."""
        if not self.users:
            raise ValueError(f"Team has no users: {self.name}")

        return self
