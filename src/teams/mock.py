from .client import TeamsClient


class MockTeamsClient(TeamsClient):
    """Resolve teams from in-memory test data."""
