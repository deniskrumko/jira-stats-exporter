# jira-stats-exporter
Export statistics from Atlassian Jira

# Config

Application config is loaded from `--config` cli arg or `JIRA_STATS_EXPORTER_CONFIG` env var.

```toml
[api]
base_url = "https://jira.best-team.org"
api_token = ""

[cli]
max_summary_length = 60

[[teams]]
name = "My best team"
shortcut = "ml"
default = true
users = [
    "krumko",
]
```

# Basic usage

- `uv run cli <command>` - run a specific command

## Commands

- `me` - show response from https://jira.kolesa-team.org/rest/api/2/myself to check if auth works
- `closed --team -m 5` - show stats for the default configured team
- `closed --team backend -w 0` - show stats for a configured team by shortcut
