from app.config import Settings


def test_settings_default():
    settings = Settings()
    assert settings.ENVIRONMENT == "development"
    assert settings.PORT == 8000
    assert settings.MODE == "cloud"
    assert settings.CACHE_THRESHOLD == 0.96
    assert settings.GUARDS == "on"
    assert settings.GRAPH_MAX_EXPANSION == 4
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_settings_phase_validation():
    # In phase 1, no cloud API keys required
    settings = Settings(MODE="cloud", GROQ_API_KEY=None, CLERK_SECRET_KEY=None, SUPABASE_URL=None, SUPABASE_SERVICE_ROLE_KEY=None)
    missing = settings.validate_phase_keys(phase=1)
    assert missing == []

    # In phase 2 cloud mode, GROQ_API_KEY is required
    missing_phase2 = settings.validate_phase_keys(phase=2)
    assert "GROQ_API_KEY" in missing_phase2

    # In phase 5, Clerk and Supabase keys required
    missing_phase5 = settings.validate_phase_keys(phase=5)
    assert "CLERK_SECRET_KEY" in missing_phase5
    assert "SUPABASE_URL" in missing_phase5
    assert "SUPABASE_SERVICE_ROLE_KEY" in missing_phase5


def test_settings_cors_comma_separated():
    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://allcited.vercel.app")
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "https://allcited.vercel.app" in settings.CORS_ORIGINS
