# Repository Guidelines

## Project Structure & Module Organization

- This is a Python 3.13 CLI project managed with `uv`
- Source code lives under `src/`
- `src/app/cli.py` defines the CLI entry point
- `src/jira/` contains Jira configuration and HTTP client logic
- `src/jira/custom_fields.py` contains Jira custom field mapping logic

## Build, Test, and Development Commands

- `uv sync --dev`: install runtime and development dependencies from `uv.lock`.
- `make fmt`: run formatting
- `make lint`: verify formatting
- `make check`: run all checks

## Coding Style

- Add docstrings to created classes, methods and functions. Docstrings only in English. Always single-line docstrings, without args/return. Only one-line summary. For `__init__` methods write """Initialize class instance.""".
- Avoid generic docstrings that start with words like "Represent"; describe the model directly.
- Use Pydantic `BaseModel` for structured data models instead of dataclasses.
- Store Pydantic models in `resources.py` files within their modules.
- Do not use `model_config = ConfigDict(frozen=True)` in Pydantic models.
- Use python 3.13 syntax
- Run `make fmt` to format code

## Testing Guidelines

- Use `pytest` for unit tests
- Add tests to `tests/` and use only plain files without sub-dir. For example: `tests/test_jira.py`.
- Add fixtures to `tests/conftest.py`. Prefer using fixtures.

## Security & Configuration Tips

- Never commit Jira tokens, `.env` files, or local virtual environments
