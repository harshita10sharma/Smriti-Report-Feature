import pytest

from analysis.config import load_settings
from analysis.errors import ConfigurationError


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "REPORT_ENGINE_LOG_LEVEL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "INTERNAL_SHARED_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults_when_nothing_is_set() -> None:
    settings = load_settings()
    assert settings.log_level == "INFO"
    assert settings.supabase_url is None
    assert settings.supabase_service_role_key is None
    assert settings.internal_shared_secret is None


def test_invalid_log_level_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPORT_ENGINE_LOG_LEVEL", "NOT_A_LEVEL")
    with pytest.raises(ConfigurationError):
        load_settings()


def test_require_supabase_raises_when_only_one_value_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    settings = load_settings()
    with pytest.raises(ConfigurationError):
        settings.require_supabase()


def test_require_supabase_succeeds_when_both_values_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-only-placeholder")
    settings = load_settings()
    url, key = settings.require_supabase()
    assert url == "https://example.supabase.co"
    assert key == "test-only-placeholder"


def test_require_internal_shared_secret_raises_when_unset() -> None:
    settings = load_settings()
    with pytest.raises(ConfigurationError):
        settings.require_internal_shared_secret()
