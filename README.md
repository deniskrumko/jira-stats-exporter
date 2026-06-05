# jira-stats-exporter

Export statistics from Atlassian Jira.

# Config

Application config is loaded from `--config` cli arg or `JIRA_STATS_EXPORTER_CONFIG` env var.

```toml
[api]
base_url = "https://jira.best-team.org"
api_token = "<your_api_token>"

[cli]
max_summary_length = 120

[teams.backend]
name = "Backend team"
default = true
users = [
    "krumko",
]
```

# Basic usage

- `uv run cli <command>` - run a specific command

## Commands

- `me` - show response from `<jira_base_url>/rest/api/2/myself` to check if auth works
- `issue <issue_id>` - show details for a specific issue
- `closed --week 0` - show closed issues for the current week
- `closed --team backend --quarter -1` - show closed issues for past quarter for team backend
