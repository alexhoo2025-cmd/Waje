from __future__ import annotations

from tools.gemini_model_routing import classify_model_attempt, model_candidates


def test_candidates_are_preferences_and_end_with_cli_default() -> None:
    config = {
        "preferred_models": {"default": "gemini-preferred"},
        "model_fallback": {
            "enabled": True,
            "models": ["gemini-preferred", "gemini-backup"],
            "allow_cli_default": True,
            "max_attempts": 5,
        },
    }
    assert model_candidates(config) == ["gemini-preferred", "gemini-backup", None]


def test_permission_failure_does_not_retry_by_changing_model() -> None:
    status, retryable = classify_model_attempt(1, "403 aiplatform.endpoints.predict permission denied")
    assert status == "blocked_iam"
    assert retryable is False


def test_unavailable_model_is_retryable() -> None:
    status, retryable = classify_model_attempt(1, "model gemini-3.7-flash not found")
    assert status == "model_unavailable"
    assert retryable is True

