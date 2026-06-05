import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

CONFIG_ENV_VAR = "JIRA_STATS_EXPORTER_CONFIG"
DEFAULT_CONFIG_FILE_NAME = "config.toml"


class TeamConfig(BaseModel):
    """Configure a Jira team."""

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


class CLIConfig(BaseModel):
    """Configure console application behavior."""

    max_summary_length: int = 100


class AppConfig(BaseModel):
    """Configure the Jira stats exporter."""

    cli: CLIConfig = Field(default_factory=CLIConfig)
    teams: list[TeamConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_teams(self) -> "AppConfig":
        """Validate configured teams."""
        default_teams = [team for team in self.teams if team.default]
        if len(default_teams) > 1:
            raise ValueError("Only one default team can be configured")

        shortcuts = [team.shortcut for team in self.teams]
        if len(shortcuts) != len(set(shortcuts)):
            raise ValueError("Team shortcuts must be unique")

        names = [team.name for team in self.teams]
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


def resolve_config_path(path: Path | None = None) -> Path:
    """Resolve application configuration path."""
    if path is not None:
        return path.expanduser()

    env_path = os.getenv(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()

    return Path(__file__).resolve().parents[2] / DEFAULT_CONFIG_FILE_NAME
