# jira-stats-exporter
Export statistics from Atlassian Jira

# Env vars

For work this CLI required 2 env vars:
- `JIRA_BASE_URL`
- `JIRA_API_TOKEN`
- `JIRA_STATS_EXPORTER_CONFIG` - optional path to `config.toml`

If env vars not set, CLI will try to read them from `~/.secrets/jira-stats-exporter/.env` as default path

# Config

Application config is loaded from `--config`, `JIRA_STATS_EXPORTER_CONFIG`, or `config.toml`
near the application files.

```toml
[[team]]
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
- `closed --team ml -m 5` - show stats for a configured team by shortcut or name
