from app.core.config import get_settings


def test_settings_load_from_json():
    settings = get_settings()
    assert settings.app_name == "PratikAI"
    assert settings.phase >= 1
    assert settings.default_entity == "friday"


def test_settings_are_cached_singleton():
    assert get_settings() is get_settings()


def test_database_path_resolves_under_project_root():
    settings = get_settings()
    resolved = settings.database.resolved_path()
    assert resolved.is_absolute()
    assert resolved.name.endswith(".db")
