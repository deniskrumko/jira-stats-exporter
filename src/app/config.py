import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from jira.config import JiraAPIConfig
from teams import Team
from users import UsersConfig

CONFIG_ENV_VAR = "JIRA_STATS_EXPORTER_CONFIG"
DEFAULT_CONFIG_FILE_NAME = "config.toml"


class CLIConfig(BaseModel):
    """Configure console application behavior."""

    max_summary_length: int = 100


class AppConfig(BaseModel):
    """Configure the Jira stats exporter."""

    api: JiraAPIConfig = Field(default_factory=JiraAPIConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    users: UsersConfig = Field(default_factory=UsersConfig)
    teams: dict[str, Team] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_teams(self) -> "AppConfig":
        """Validate configured teams."""
        default_teams = [team for team in self.teams.values() if team.default]
        if len(default_teams) > 1:
            raise ValueError("Only one default team can be configured")

        names = [team.name for team in self.teams.values()]
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
        try:
            return cls.model_validate(payload)
        except Exception as e:
            raise ValueError(f"Invalid config {config_path}: {e}") from e


def resolve_config_path(path: Path | None = None) -> Path:
    """Resolve application configuration path."""
    if path is not None:
        return path.expanduser()

    env_path = os.getenv(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()

    raise ValueError(
        "Specify config path via --config or set JIRA_STATS_EXPORTER_CONFIG environment variable"
    )
