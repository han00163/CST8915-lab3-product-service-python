import pytest

from product_service.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in ("HOST", "PORT", "WORKERS", "LOG_LEVEL", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)


def test_service_runs_with_defaults_without_external_resources():
    settings = Settings.from_env()
    assert (settings.host, settings.port, settings.workers) == ("0.0.0.0", 3030, 1)
    assert settings.log_level == "info"
    assert settings.cors_origins == ("*",)


def test_environment_controls_deployment(monkeypatch):
    values = {
        "HOST": "127.0.0.1",
        "PORT": "4040",
        "WORKERS": "2",
        "LOG_LEVEL": "WARNING",
        "CORS_ORIGINS": "https://one.example, https://two.example",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    settings = Settings.from_env()
    assert (settings.host, settings.port, settings.workers) == ("127.0.0.1", 4040, 2)
    assert settings.log_level == "warning"
    assert settings.cors_origins == ("https://one.example", "https://two.example")


def test_local_dotenv_never_overrides_injected_config(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("PORT=5050\nWORKERS=2\n")
    monkeypatch.setenv("PORT", "6060")
    settings = Settings.from_env()
    assert settings.port == 6060
    assert settings.workers == 2


def test_parent_dotenv_is_not_loaded(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PORT=5050\n")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    assert Settings.from_env().port == 3030


def test_cors_can_be_disabled(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "")
    assert Settings.from_env().cors_origins == ()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("PORT", "abc"),
        ("PORT", "0"),
        ("PORT", "65536"),
        ("WORKERS", "0"),
        ("WORKERS", "129"),
        ("LOG_LEVEL", "nonsense"),
        ("HOST", " "),
    ],
)
def test_invalid_configuration_fails_clearly(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        Settings.from_env()
