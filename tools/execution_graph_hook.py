"""Best-effort execution graph event hook for report pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from execution_graph import record_and_refresh


def emit(
    root: Path,
    *,
    job_id: str,
    run_id: str,
    phase: str,
    status: str,
    receipts: Iterable[str] = (),
    artifacts: Iterable[str] = (),
) -> dict:
    try:
        return {"status": "ok", **record_and_refresh(
            root,
            job_id=job_id,
            run_id=run_id,
            phase=phase,
            status=status,
            receipt_paths=receipts,
            artifact_paths=artifacts,
        )}
    except Exception as exc:
        return {"status": "degraded", "error_type": type(exc).__name__}
