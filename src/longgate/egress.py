from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .pii import scan_structured_strings, scan_text
from .policy import PolicyDecision


def _stage_json_text(
    payload_text: str,
    out_dir: Path,
    decision: PolicyDecision,
    *,
    payload_name: str,
    manifest_name: str,
) -> tuple[Path | None, dict[str, object]]:
    """Stage JSON after a final local PII scan. No network request is made."""
    egress_dir = out_dir / "egress"
    egress_dir.mkdir(parents=True, exist_ok=True)
    scan = {"passed": False, "pii_hits": 0, "by_entity": {}}
    manifest = egress_dir / manifest_name

    if not decision.allow:
        manifest.write_text(
            json.dumps(
                {**decision.to_dict(), "final_scan": scan},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return None, scan

    findings = scan_text(payload_text)
    scan = {
        "passed": findings.total_hits == 0,
        "pii_hits": findings.total_hits,
        "by_entity": findings.by_entity,
    }
    effective_allow = decision.allow and bool(scan["passed"])
    manifest.write_text(
        json.dumps(
            {
                **decision.to_dict(),
                "allow_after_final_scan": effective_allow,
                "final_scan": scan,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if not effective_allow:
        return None, scan

    payload = egress_dir / payload_name
    payload.write_text(payload_text, encoding="utf-8")
    return payload, scan


def stage_json_egress(
    payload: dict[str, Any],
    out_dir: Path,
    decision: PolicyDecision,
    *,
    payload_name: str = "safe_aggregate.json",
    manifest_name: str = "aggregate_egress_manifest.json",
) -> tuple[Path | None, dict[str, object]]:
    payload_text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    egress_dir = out_dir / "egress"
    egress_dir.mkdir(parents=True, exist_ok=True)
    scan_findings = scan_structured_strings(payload)
    scan = {
        "passed": scan_findings.total_hits == 0,
        "pii_hits": scan_findings.total_hits,
        "by_entity": scan_findings.by_entity,
    }
    effective_allow = decision.allow and bool(scan["passed"])
    (egress_dir / manifest_name).write_text(
        json.dumps(
            {
                **decision.to_dict(),
                "allow_after_final_scan": effective_allow,
                "final_scan": scan,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if not effective_allow:
        return None, scan
    path = egress_dir / payload_name
    path.write_text(payload_text, encoding="utf-8")
    return path, scan


def stage_egress(
    df: pd.DataFrame,
    out_dir: Path,
    decision: PolicyDecision,
) -> tuple[Path | None, dict[str, object]]:
    """Stage row-level synthetic JSON after a final local PII rescan."""
    payload_text = df.to_json(
        orient="records",
        force_ascii=False,
        indent=2,
    )
    return _stage_json_text(
        payload_text,
        out_dir,
        decision,
        payload_name="safe_payload.json",
        manifest_name="egress_manifest.json",
    )
