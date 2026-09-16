from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .utils import sha256_file, write_json

DEFAULT_ARTIFACTS = (
    "manifest.json",
    "audit.json",
    "safe/synthetic.csv",
    "egress/egress_manifest.json",
    "egress/safe_payload.json",
    "report/trust-report.html",
)


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_provenance(
    run_dir: str | Path,
    artifacts: tuple[str, ...] = DEFAULT_ARTIFACTS,
) -> Path:
    root = Path(run_dir)
    records: list[dict[str, object]] = []
    for relative in artifacts:
        path = root / relative
        if not path.is_file():
            continue
        records.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )

    core = {
        "format": "long-gate-provenance-v1",
        "artifacts": records,
    }
    document = {
        **core,
        "integrity_digest": _canonical_digest(core),
        "signature": None,
        "signature_note": (
            "Integrity-verifiable SHA-256 manifest. This is not a digital "
            "signature and does not authenticate the machine or maintainer."
        ),
    }
    out = root / "provenance.json"
    write_json(out, document)
    return out


def verify_provenance(run_dir: str | Path) -> dict[str, object]:
    root = Path(run_dir)
    path = root / "provenance.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    core = {
        "format": document["format"],
        "artifacts": document["artifacts"],
    }
    expected_digest = _canonical_digest(core)
    mismatches: list[dict[str, str]] = []

    for item in document["artifacts"]:
        artifact = root / item["path"]
        if not artifact.is_file():
            mismatches.append(
                {
                    "path": item["path"],
                    "reason": "missing",
                }
            )
            continue
        actual = sha256_file(artifact)
        if actual != item["sha256"]:
            mismatches.append(
                {
                    "path": item["path"],
                    "reason": "sha256_mismatch",
                }
            )

    digest_matches = expected_digest == document.get("integrity_digest")
    return {
        "valid": digest_matches and not mismatches,
        "integrity_digest_matches": digest_matches,
        "mismatches": mismatches,
        "artifact_count": len(document["artifacts"]),
    }
