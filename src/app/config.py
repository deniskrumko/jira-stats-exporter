import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONFIG_ENV_VAR = "JIRA_STATS_EXPORTER_CONFIG"
DEFAULT_CONFIG_FILE_NAME = "config.toml"


class TeamConfig(BaseModel):
    """Configure a Jira team."""

    model_config = ConfigDict(frozen=True)

    name: str
    shortcut: str
    default: bool = False
    users: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_users(self) -> "TeamConfig":
        """Validate configured team users."""
        if not self.users:
            raise ValueError(f"Team has no users: {self.name}")
        return self


class AppConfig(BaseModel):
    """Configure the Jira stats exporter."""

    model_config = ConfigDict(frozen=True)

    team: list[TeamConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_teams(self) -> "AppConfig":
        """Validate configured teams."""
        default_teams = [team for team in self.team if team.default]
        if len(default_teams) > 1:
            raise ValueError("Only one default team can be configured")

        shortcuts = [team.shortcut for team in self.team]
        if len(shortcuts) != len(set(shortcuts)):
            raise ValueError("Team shortcuts must be unique")

        names = [team.name for team in self.team]
        if len(names) != len(set(names)):
            raise ValueError("Team names must be unique")

        return self

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        """Load application configuration from TOML."""
        config_path = resolve_config_path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file does not exist: {config_path}")

        payload = tomllib.loads(config_path.read_text())
        return cls.model_validate(payload)

    def resolve_team(self, value: str | None = None) -> TeamConfig:
        """Resolve a configured team by name, shortcut, or default marker."""
        if value is None:
            default_teams = [team for team in self.team if team.default]
            if not default_teams:
                raise ValueError("Default team is not configured")
            return default_teams[0]

        for team in self.team:
            if value in (team.shortcut, team.name):
                return team

        raise ValueError(f"Team is not configured: {value}")


def resolve_config_path(path: Path | None = None) -> Path:
    """Resolve application configuration path."""
    if path is not None:
        return path.expanduser()

    env_path = os.getenv(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()

    return Path(__file__).resolve().parents[2] / DEFAULT_CONFIG_FILE_NAME
