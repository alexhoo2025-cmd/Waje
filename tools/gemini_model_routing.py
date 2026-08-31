"""Enterprise Gemini model selection and bounded fallback helpers.

Model names are preferences, not hard requirements.  The caller still owns
the enterprise-authentication and BigQuery safety gates; this module only
decides which model flag to pass to the CLI and when a retry with another
model is reasonable.
"""

from __future__ import annotations

from typing import Any


DEFAULT_FALLBACK_MODELS = (
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
)


def _as_model_name(value: Any) -> str | None:
    if value is None:
        return None
    name = str(value).strip()
    return name or None


def model_routing_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return normalized model fallback settings.

    ``model_fallback`` may remain the legacy string ``"auto"``.  A mapping
    can opt into an explicit candidate list and CLI-default fallback without
    changing callers that only provide ``preferred_models``.
    """

    raw = config.get("model_fallback", "auto")
    if isinstance(raw, dict):
        enabled = raw.get("enabled", True) is not False
        configured = raw.get("models", raw.get("fallback_models", []))
        allow_cli_default = raw.get("allow_cli_default", True) is not False
        max_attempts = raw.get("max_attempts", 5)
    else:
        enabled = str(raw).lower() in {"auto", "true", "1", "enabled", "on"}
        configured = config.get("model_candidates", [])
        allow_cli_default = config.get("allow_cli_default_model", True) is not False
        max_attempts = config.get("model_fallback_max_attempts", 5)

    if not isinstance(configured, list):
        configured = []
    try:
        max_attempts = max(1, min(int(max_attempts), 8))
    except (TypeError, ValueError):
        max_attempts = 5
    return {
        "enabled": enabled,
        "configured_models": [_as_model_name(item) for item in configured if _as_model_name(item)],
        "allow_cli_default": allow_cli_default,
        "max_attempts": max_attempts,
    }


def model_candidates(config: dict[str, Any], model_key: str = "default") -> list[str | None]:
    """Build an ordered, deduplicated list; ``None`` means CLI default."""

    preferred_models = config.get("preferred_models") or {}
    preferred = _as_model_name(preferred_models.get(model_key, preferred_models.get("default")))
    routing = model_routing_config(config)
    candidates: list[str | None] = []

    def add(value: str | None) -> None:
        if value is not None and value not in candidates:
            candidates.append(value)

    add(preferred)
    if routing["enabled"]:
        configured = routing["configured_models"] or list(DEFAULT_FALLBACK_MODELS)
        for value in configured:
            add(value)
    if not candidates:
        add(None)
    if routing["enabled"] and routing["allow_cli_default"] and None not in candidates:
        candidates.append(None)
    return candidates[: int(routing["max_attempts"])]


def classify_model_attempt(returncode: int, stderr: str, *, timed_out: bool = False) -> tuple[str, bool]:
    """Classify a failed CLI attempt and indicate whether another model may help."""

    lowered = (stderr or "").lower()
    if "aiplatform.endpoints.predict" in lowered or ("permission" in lowered and "denied" in lowered):
        return "blocked_iam", False
    if "subscription" in lowered or "license" in lowered or "cloudaicompanion.licenses.selfassign" in lowered:
        return "blocked_license", False
    if timed_out or returncode == 124 or "deadline exceeded" in lowered or "timed out" in lowered:
        return "failed_timeout", True
    model_words = ("model", "gemini-")
    unavailable_words = ("not found", "not available", "unsupported", "unknown", "invalid", "does not exist", "404")
    if any(word in lowered for word in model_words) and any(word in lowered for word in unavailable_words):
        return "model_unavailable", True
    if any(word in lowered for word in ("temporarily unavailable", "service unavailable", "503", "429", "resource exhausted")):
        return "model_transient", True
    return "failed", False


def retryable_model_status(status: str) -> bool:
    return status in {"model_unavailable", "model_transient", "failed_timeout", "failed_invalid_json"}

