from pathlib import Path

from app import config
from app.config import CONFIG_ENV_VAR, DEFAULT_CONFIG_FILE_NAME, resolve_config_path


def test_resolve_config_path_prefers_explicit_path(tmp_path: Path) -> None:
    """Resolve explicit config path before other sources."""
    path = tmp_path / "config.toml"

    assert resolve_config_path(path) == path


def test_resolve_config_path_reads_env_var(tmp_path: Path, monkeypatch) -> None:
    """Resolve config path from environment variable."""
    path = tmp_path / "env-config.toml"
    monkeypatch.setenv(CONFIG_ENV_VAR, str(path))

    assert resolve_config_path() == path


def test_resolve_config_path_uses_application_directory(tmp_path: Path, monkeypatch) -> None:
    """Resolve default config path relative to the application files."""
    monkeypatch.chdir(tmp_path)

    assert (
        resolve_config_path()
        == Path(config.__file__).resolve().parents[2] / DEFAULT_CONFIG_FILE_NAME
    )
