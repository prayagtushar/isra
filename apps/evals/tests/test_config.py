from src.config import settings


def test_defaults_present():
    assert settings.llm_model
    assert settings.openrouter_base_url.startswith("https://")
