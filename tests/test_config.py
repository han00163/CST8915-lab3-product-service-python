import pytest

from product_service.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in (
        "DATABASE_URL",
        "HOST",
        "PORT",
        "WORKERS",
        "LOG_LEVEL",
        "CORS_ORIGINS",
        "DB_CONNECT_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def test_required_database_url():
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        Settings.from_env()


def test_environment_controls_deployment(monkeypatch):
    values = {
        "DATABASE_URL": "postgresql+psycopg://user:secret@remote.example/catalog",
        "HOST": "127.0.0.1",
        "PORT": "4040",
        "WORKERS": "2",
        "LOG_LEVEL": "WARNING",
        "CORS_ORIGINS": "https://one.example, https://two.example",
        "DB_CONNECT_TIMEOUT": "3",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    settings = Settings.from_env()
    assert settings.database_url == values["DATABASE_URL"]
    assert (settings.host, settings.port, settings.workers) == ("127.0.0.1", 4040, 2)
    assert settings.log_level == "warning"
    assert settings.cors_origins == ("https://one.example", "https://two.example")
    assert settings.db_connect_timeout == 3
    assert "secret" not in repr(settings)


def test_local_dotenv_never_overrides_injected_config(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///local.db\nPORT=5050\n")
    monkeypatch.setenv("PORT", "6060")
    assert Settings.from_env().port == 6060
    assert Settings.from_env().database_url == "sqlite:///local.db"


def test_parent_repository_dotenv_is_not_loaded(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///parent.db\n")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        Settings.from_env()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("PORT", "abc"),
        ("PORT", "0"),
        ("PORT", "65536"),
        ("WORKERS", "0"),
        ("DB_CONNECT_TIMEOUT", "0"),
        ("LOG_LEVEL", "nonsense"),
        ("HOST", " "),
        ("DATABASE_URL", "not-a-url"),
        ("DATABASE_URL", "mysql://user:secret@host/db"),
        ("DATABASE_URL", "postgresql+psycopg:///products"),
    ],
)
def test_invalid_configuration_fails_without_exposing_secrets(monkeypatch, name, value):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name) as error:
        Settings.from_env()
    assert "secret" not in str(error.value)
