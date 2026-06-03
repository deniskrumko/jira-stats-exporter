# jira-stats-exporter
Export statistics from Atlassian Jira

# Env vars

For work this CLI required 2 env vars:
- `JIRA_BASE_URL`
- `JIRA_API_TOKEN`

If env vars not set, CLI will try to read them from `~/.secrets/jira-stats-exporter/.env` as default path

# Basic usage

- `uv run cli <command>` - run a specific command

## Commands

- `me` - show response from https://jira.kolesa-team.org/rest/api/2/myself to check if auth works
