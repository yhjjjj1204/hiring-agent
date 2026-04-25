import os

_DEFAULTS = {
    "MONGODB_URI": "mongodb://ferret_hr:digging_for_gold_resumes@127.0.0.1:27017/hiring_agent",
    "MONGODB_DB": "hiring_agent",
    "HTTP_USER_AGENT_CONTACT": "admin@example.com",
    "UPLOADS_DIR": "uploads",
    "GUARDRAIL_ENABLED": "true",
    "GUARDRAIL_MODE": "enforce",
    "GUARDRAIL_CLASSIFIER_MODEL": "gpt-4o-mini",
}

def __getattr__(name):
    """
    Ensures config variables are read from the environment at runtime.
    This allows 'monkeypatch.setattr(config, "VAR", "val")' to work in tests
    because setattr adds to the module's __dict__, which is checked before __getattr__.
    """
    if name in {
        "OPENAI_API_KEY", "HIRING_AGENT_API_KEY", "MONGODB_URI", "MONGODB_DB",
        "GITHUB_TOKEN", "HTTP_USER_AGENT_CONTACT", "UPLOADS_DIR",
        "GUARDRAIL_ENABLED", "GUARDRAIL_MODE", "GUARDRAIL_CLASSIFIER_MODEL"
    }:
        val = os.getenv(name)
        if val is None:
            val = _DEFAULTS.get(name)

        if name == "GUARDRAIL_ENABLED" and val is not None:
             return str(val).lower() in {"1", "true", "yes", "on"}

        return val

    raise AttributeError(f"module {__name__} has no attribute {name}")
