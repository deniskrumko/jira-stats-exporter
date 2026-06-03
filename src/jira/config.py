import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JiraConfig:
    """Configuration required to connect to Jira."""

    base_url: str
    api_token: str

    @classmethod
    def from_env(cls) -> "JiraConfig":
        """Create Jira configuration from required environment variables."""
        missing = [name for name in ("JIRA_BASE_URL", "JIRA_API_TOKEN") if not os.getenv(name)]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required env vars: {joined}")

        return cls(
            base_url=os.environ["JIRA_BASE_URL"].rstrip("/"),
            api_token=os.environ["JIRA_API_TOKEN"],
        )
