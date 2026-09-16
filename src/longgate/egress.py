from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from .policy import PolicyDecision


def stage_egress(df: pd.DataFrame, out_dir: Path, decision: PolicyDecision) -> Path | None:
    """Stage a safe payload. v0.1 never performs a network request itself."""
    egress_dir = out_dir / "egress"
    egress_dir.mkdir(parents=True, exist_ok=True)
    manifest = egress_dir / "egress_manifest.json"
    manifest.write_text(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    if not decision.allow:
        return None
    payload = egress_dir / "safe_payload.json"
    df.to_json(payload, orient="records", force_ascii=False, indent=2)
    return payload
