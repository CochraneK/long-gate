from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .pii import scan_structured_strings, scan_text
from .policy import PolicyDecision
from .utils import sha256_file

EGRESS_MANIFEST_FORMAT = "long-gate-egress-manifest-v1"


def _manifest_payload(
    decision: PolicyDecision,
    scan: dict[str, object],
    *,
    effective_allow: bool,
    artifact_name: str | None = None,
    artifact_sha256: str | None = None,
) -> dict[str, object]:
    return {
        "format": EGRESS_MANIFEST_FORMAT,
        **decision.to_dict(),
        "allow_after_final_scan": effective_allow,
        "artifact": artifact_name,
        "artifact_sha256": artifact_sha256,
        "final_scan": scan,
    }


def _write_manifest(
    manifest: Path,
    decision: PolicyDecision,
    scan: dict[str, object],
    *,
    effective_allow: bool,
    artifact_name: str | None = None,
    artifact_sha256: str | None = None,
) -> None:
    manifest.write_text(
        json.dumps(
            _manifest_payload(
                decision,
                scan,
                effective_allow=effective_allow,
                artifact_name=artifact_name,
                artifact_sha256=artifact_sha256,
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _publish_payload(
    payload: Path,
    payload_text: str,
    manifest: Path,
    decision: PolicyDecision,
    scan: dict[str, object],
) -> Path:
    payload.write_text(payload_text, encoding="utf-8")
    try:
        digest = sha256_file(payload)
        _write_manifest(
            manifest,
            decision,
            scan,
            effective_allow=True,
            artifact_name=payload.name,
            artifact_sha256=digest,
        )
    except Exception:
        payload.unlink(missing_ok=True)
        raise
    return payload


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
    scan: dict[str, object] = {
        "passed": False,
        "pii_hits": 0,
        "by_entity": {},
    }
    manifest = egress_dir / manifest_name

    if not decision.allow:
        _write_manifest(
            manifest,
            decision,
            scan,
            effective_allow=False,
        )
        return None, scan

    findings = scan_text(payload_text)
    scan = {
        "passed": findings.total_hits == 0,
        "pii_hits": findings.total_hits,
        "by_entity": findings.by_entity,
    }
    effective_allow = decision.allow and bool(scan["passed"])
    if not effective_allow:
        _write_manifest(
            manifest,
            decision,
            scan,
            effective_allow=False,
        )
        return None, scan

    payload = egress_dir / payload_name
    return (
        _publish_payload(
            payload,
            payload_text,
            manifest,
            decision,
            scan,
        ),
        scan,
    )


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
    scan: dict[str, object] = {
        "passed": scan_findings.total_hits == 0,
        "pii_hits": scan_findings.total_hits,
        "by_entity": scan_findings.by_entity,
    }
    effective_allow = decision.allow and bool(scan["passed"])
    manifest = egress_dir / manifest_name

    if not effective_allow:
        _write_manifest(
            manifest,
            decision,
            scan,
            effective_allow=False,
        )
        return None, scan

    path = egress_dir / payload_name
    return (
        _publish_payload(
            path,
            payload_text,
            manifest,
            decision,
            scan,
        ),
        scan,
    )


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
