from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from .pii import scan_text
from .policy import PolicyDecision


def stage_egress(df: pd.DataFrame, out_dir: Path, decision: PolicyDecision) -> tuple[Path | None, dict[str, object]]:
    """Stage a safe payload after a final local PII rescan. No network request is made."""
    egress_dir = out_dir / "egress"
    egress_dir.mkdir(parents=True, exist_ok=True)
    scan = {"passed": False, "pii_hits": 0, "by_entity": {}}
    manifest = egress_dir / "egress_manifest.json"

    if not decision.allow:
        manifest.write_text(
            json.dumps({**decision.to_dict(), "final_scan": scan}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return None, scan

    payload_text = df.to_json(orient="records", force_ascii=False, indent=2)
    findings = scan_text(payload_text)
    scan = {
        "passed": findings.total_hits == 0,
        "pii_hits": findings.total_hits,
        "by_entity": findings.by_entity,
    }
    effective_allow = decision.allow and bool(scan["passed"])
    manifest.write_text(
        json.dumps(
            {**decision.to_dict(), "allow_after_final_scan": effective_allow, "final_scan": scan},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if not effective_allow:
        return None, scan

    payload = egress_dir / "safe_payload.json"
    payload.write_text(payload_text, encoding="utf-8")
    return payload, scan
