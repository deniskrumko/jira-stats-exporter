from pydantic import BaseModel

from app.resources import IssueGroup
from users import User


class UserReport(BaseModel):
    """Collect report issue groups for one Jira user."""

    user: User
    closed: IssueGroup
    kpi: IssueGroup
    in_progress: IssueGroup
    created: IssueGroup
