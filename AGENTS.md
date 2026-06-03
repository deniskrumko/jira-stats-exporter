# Repository Guidelines

## Project Structure & Module Organization

- This is a Python 3.13 CLI project managed with `uv`
- Source code lives under `src/`
- `src/app/cli.py` defines the CLI entry point
- `src/jira/` contains Jira configuration and HTTP client logic
- `src/custom_fields/` contains Jira custom field mapping logic

## Build, Test, and Development Commands

- `uv sync --dev`: install runtime and development dependencies from `uv.lock`.
- `make fmt`: run formatting
- `make lint`: verify formatting
- `make check`: run all checks

The CLI requires `JIRA_BASE_URL` and `JIRA_API_TOKEN`. If they are not exported in the shell, `src/app/cli.py` loads `~/.secrets/jira-stats-exporter/.env`.

## Coding Style

- Add docstrings to created classes, methods and functions. Docstrings only in English. Always single-line docstrings, without args/return. Only one-line summary. For `__init__` methods write """Initialize class instance.""".
- Use python 3.13 syntax
- Run `make fmt` to format code

## Testing Guidelines

- No tests for now

## Security & Configuration Tips

- Never commit Jira tokens, `.env` files, or local virtual environments
