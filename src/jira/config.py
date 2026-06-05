import os
from functools import partial

from pydantic import BaseModel, Field


class JiraAPIConfig(BaseModel):
    """Configuration required to connect to Jira."""

    api_token: str | None = Field(default_factory=partial(os.getenv, "JIRA_API_TOKEN"))
    base_url: str | None = Field(default_factory=partial(os.getenv, "JIRA_BASE_URL"))
