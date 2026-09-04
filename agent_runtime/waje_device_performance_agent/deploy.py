"""Deploy the Waje device-performance ADK application to Agent Runtime.

This module never creates a BigQuery dataset, grants IAM roles, or enables an
API. It expects those operations to be completed and verified by a data
platform administrator before deployment. It also never writes credentials to
disk: Application Default Credentials or an Agent Identity are required.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from typing import Any

from .agent import AGENT_DISPLAY_NAME, build_app
from .config import FALLBACK_MODEL, MODEL_LOCATION, PRIMARY_MODEL, THINKING_LEVEL


class ModelProbeError(RuntimeError):
    """No approved model could be verified for a deployment."""


def model_candidates() -> tuple[str, str]:
    return (PRIMARY_MODEL, FALLBACK_MODEL)


def select_deployment_model(probe: Callable[[str], None]) -> tuple[str, str | None]:
    """Probe the ordered models once; only model availability may trigger fallback."""

    primary_error: str | None = None
    for model in model_candidates():
        try:
            probe(model)
            return model, primary_error
        except ModelProbeError as exc:
            if model == PRIMARY_MODEL and str(exc).startswith(("model_unavailable:", "model_transient:")):
                primary_error = str(exc)
                continue
            raise
    raise ModelProbeError("no_approved_model_available")


def probe_model(project_id: str, model: str) -> None:
    """Run a non-data model availability probe using enterprise authentication."""

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # pragma: no cover - deployment dependency
        raise ModelProbeError("google_genai_library_unavailable") from exc
    try:
        client = genai.Client(enterprise=True, project=project_id, location=MODEL_LOCATION)
        client.models.generate_content(
            model=model,
            contents="Return only the word ready.",
            config=types.GenerateContentConfig(
                max_output_tokens=16,
                thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
            ),
        )
    except Exception as exc:  # pragma: no cover - depends on cloud IAM
        text = str(exc).lower()
        if "permission" in text or "unauthenticated" in text or "forbidden" in text:
            raise ModelProbeError(f"non_retryable_model_probe_failure:{model}") from exc
        if any(token in text for token in ("temporarily unavailable", "service unavailable", "429", "503", "deadline exceeded", "timed out")):
            raise ModelProbeError(f"model_transient:{model}") from exc
        if any(token in text for token in ("not found", "not available", "unsupported", "404", "model")):
            raise ModelProbeError(f"model_unavailable:{model}") from exc
        raise ModelProbeError(f"non_retryable_model_probe_failure:{model}") from exc


def deploy(
    *,
    project_id: str,
    runtime_location: str,
    staging_bucket: str,
    active_model: str,
) -> dict[str, str]:
    """Create one Agent Runtime deployment using Agent Identity."""

    try:
        import vertexai
        from vertexai import types
    except ImportError as exc:  # pragma: no cover - deployment dependency
        raise RuntimeError("agent_runtime_dependencies_unavailable") from exc
    if active_model not in model_candidates():
        raise RuntimeError("configured_agent_model_not_allowed")
    client = vertexai.Client(project=project_id, location=runtime_location)
    app = build_app(model=active_model)
    remote_agent = client.agent_engines.create(
        agent=app,
        config={
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112",
                "google-cloud-bigquery>=3.0",
                "google-genai>=1.0",
            ],
            "staging_bucket": staging_bucket,
            "identity_type": types.IdentityType.AGENT_IDENTITY,
            "display_name": AGENT_DISPLAY_NAME,
            "description": "Aggregate-only Firebase/GA4 Android, iOS and H5 device-performance analyst.",
            "labels": {
                "product": "waje",
                "domain": "device-performance",
                "privacy": "aggregate-only",
                "pilot": "robin-only",
            },
        },
    )
    return {
        "status": "deployed",
        "resource_name": str(remote_agent.api_resource.name),
        "model": active_model,
        "runtime_location": runtime_location,
        "thinking_level": THINKING_LEVEL,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Waje device-performance Agent Runtime application")
    parser.add_argument("--project", default="wajenigeria")
    parser.add_argument("--runtime-location", default="us-west1")
    parser.add_argument("--staging-bucket", required=True, help="Existing gs:// bucket used only for Agent Runtime deployment artifacts")
    parser.add_argument("--probe-model", action="store_true", help="Probe the approved Agent Studio model and its approved fallback before deployment")
    parser.add_argument("--dry-run", action="store_true", help="Print the deployment contract without creating an Agent Runtime resource")
    args = parser.parse_args()

    selected = PRIMARY_MODEL
    fallback_reason: str | None = None
    if args.probe_model:
        selected, fallback_reason = select_deployment_model(lambda model: probe_model(args.project, model))
    payload: dict[str, Any] = {
        "project": args.project,
        "runtime_location": args.runtime_location,
        "staging_bucket": args.staging_bucket,
        "model": selected,
        "fallback_reason": fallback_reason,
        "identity_type": "AGENT_IDENTITY",
        "privacy": "aggregate_only",
    }
    if args.dry_run:
        payload["status"] = "dry_run"
    else:
        payload.update(
            deploy(
                project_id=args.project,
                runtime_location=args.runtime_location,
                staging_bucket=args.staging_bucket,
                active_model=selected,
            )
        )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
