from __future__ import annotations

import base64
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
    "egress/aggregate_egress_manifest.json",
    "egress/safe_aggregate.json",
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


def _artifact_within_run(root: Path, relative: object) -> tuple[str, Path]:
    """Resolve an artifact path without allowing absolute or parent escape."""
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("artifact path must be a non-empty relative string")
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("artifact path must be relative")
    resolved_root = root.resolve()
    candidate = (resolved_root / rel).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("artifact path escapes the run directory") from exc
    return relative, candidate


def build_provenance(
    run_dir: str | Path,
    artifacts: tuple[str, ...] = DEFAULT_ARTIFACTS,
) -> Path:
    root = Path(run_dir)
    records: list[dict[str, object]] = []
    for relative in artifacts:
        _, path = _artifact_within_run(root, relative)
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


def verify_provenance(
    run_dir: str | Path,
    public_key_path: str | Path | None = None,
) -> dict[str, object]:
    root = Path(run_dir).resolve()
    path = root / "provenance.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    artifacts = document.get("artifacts")
    if document.get("format") != "long-gate-provenance-v1" or not isinstance(
        artifacts,
        list,
    ):
        return {
            "valid": False,
            "integrity_valid": False,
            "authenticated": False,
            "verification_scope": "integrity_only",
            "integrity_digest_matches": False,
            "mismatches": [
                {
                    "path": "provenance.json",
                    "reason": "invalid_provenance_format",
                }
            ],
            "artifact_count": 0,
            "signature": {
                "present": (root / "provenance.sig.json").is_file(),
                "valid": None,
                "reason": "provenance_invalid",
            },
            "note": "Provenance document is malformed or uses an unsupported format.",
        }

    core = {
        "format": document["format"],
        "artifacts": artifacts,
    }
    expected_digest = _canonical_digest(core)
    mismatches: list[dict[str, str]] = []

    for item in artifacts:
        if not isinstance(item, dict):
            mismatches.append(
                {
                    "path": "<invalid>",
                    "reason": "invalid_artifact_record",
                }
            )
            continue
        relative = item.get("path")
        expected_sha = item.get("sha256")
        display_path = relative if isinstance(relative, str) else "<invalid>"
        if not isinstance(expected_sha, str):
            mismatches.append(
                {
                    "path": display_path,
                    "reason": "invalid_artifact_record",
                }
            )
            continue
        try:
            _, artifact = _artifact_within_run(root, relative)
        except ValueError:
            mismatches.append(
                {
                    "path": display_path,
                    "reason": "path_outside_run",
                }
            )
            continue
        if not artifact.is_file():
            mismatches.append(
                {
                    "path": display_path,
                    "reason": "missing",
                }
            )
            continue
        actual = sha256_file(artifact)
        if actual != expected_sha:
            mismatches.append(
                {
                    "path": display_path,
                    "reason": "sha256_mismatch",
                }
            )

    digest_matches = expected_digest == document.get("integrity_digest")
    integrity_valid = digest_matches and not mismatches
    signature = (
        verify_provenance_signature(
            root,
            public_key_path,
        )
        if public_key_path is not None
        else {
            "present": (root / "provenance.sig.json").is_file(),
            "valid": None,
            "reason": "public_key_not_supplied",
        }
    )
    signature_verified = (
        bool(signature.get("valid"))
        if public_key_path is not None
        else False
    )
    overall_valid = (
        integrity_valid
        and (
            signature_verified
            if public_key_path is not None
            else True
        )
    )
    return {
        "valid": overall_valid,
        "integrity_valid": integrity_valid,
        "authenticated": integrity_valid and signature_verified,
        "verification_scope": (
            "signed_authenticity"
            if public_key_path is not None and signature_verified
            else "integrity_only"
        ),
        "integrity_digest_matches": digest_matches,
        "mismatches": mismatches,
        "artifact_count": len(artifacts),
        "signature": signature,
        "note": (
            "Unsigned verification checks internal artifact/manifest consistency only; "
            "it does not authenticate the run or detect coordinated artifact + manifest replacement."
            if public_key_path is None
            else "Signed verification additionally authenticates the provenance digest against the supplied trusted public key."
        ),
    }


def _signature_message(integrity_digest: str) -> bytes:
    return (
        "long-gate-provenance-v1\n"
        + integrity_digest
    ).encode("utf-8")


def _load_ed25519_private_key(path: str | Path):
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise RuntimeError(
            "Signed provenance requires the optional attestation dependency: "
            "pip install 'long-gate[attestation]'"
        ) from exc

    raw = Path(path).read_bytes()
    key = serialization.load_pem_private_key(
        raw,
        password=None,
    )
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Private key must be an Ed25519 PEM key.")
    return key


def _load_ed25519_public_key(path: str | Path):
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise RuntimeError(
            "Signed provenance requires the optional attestation dependency: "
            "pip install 'long-gate[attestation]'"
        ) from exc

    raw = Path(path).read_bytes()
    key = serialization.load_pem_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Public key must be an Ed25519 PEM key.")
    return key


def _ed25519_key_id(public_key: object) -> str:
    from cryptography.hazmat.primitives import serialization

    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def sign_provenance(
    run_dir: str | Path,
    private_key_path: str | Path,
) -> Path:
    root = Path(run_dir)
    provenance_path = root / "provenance.json"
    document = json.loads(
        provenance_path.read_text(encoding="utf-8")
    )
    verification = verify_provenance(root)
    if not verification["valid"]:
        raise ValueError(
            "Refusing to sign invalid or tampered provenance."
        )

    digest = str(document["integrity_digest"])
    private_key = _load_ed25519_private_key(
        private_key_path
    )
    public_key = private_key.public_key()
    signature = private_key.sign(
        _signature_message(digest)
    )
    payload = {
        "format": "long-gate-signature-v1",
        "algorithm": "ed25519",
        "signed_integrity_digest": digest,
        "key_id": _ed25519_key_id(public_key),
        "signature_base64": base64.b64encode(
            signature
        ).decode("ascii"),
        "note": (
            "Authenticity depends on independently trusting the matching "
            "public key. This does not attest the host OS or execution environment."
        ),
    }
    out = root / "provenance.sig.json"
    write_json(out, payload)
    return out


def verify_provenance_signature(
    run_dir: str | Path,
    public_key_path: str | Path,
) -> dict[str, object]:
    root = Path(run_dir)
    provenance_path = root / "provenance.json"
    signature_path = root / "provenance.sig.json"
    if not signature_path.is_file():
        return {
            "present": False,
            "valid": False,
            "reason": "signature_missing",
        }

    provenance = json.loads(
        provenance_path.read_text(encoding="utf-8")
    )
    signature = json.loads(
        signature_path.read_text(encoding="utf-8")
    )
    if signature.get("format") != "long-gate-signature-v1":
        return {
            "present": True,
            "valid": False,
            "reason": "unsupported_signature_format",
        }
    if signature.get("algorithm") != "ed25519":
        return {
            "present": True,
            "valid": False,
            "reason": "unsupported_algorithm",
        }

    digest = str(provenance.get("integrity_digest", ""))
    if signature.get("signed_integrity_digest") != digest:
        return {
            "present": True,
            "valid": False,
            "reason": "signed_digest_mismatch",
        }

    public_key = _load_ed25519_public_key(
        public_key_path
    )
    expected_key_id = _ed25519_key_id(
        public_key
    )
    if signature.get("key_id") != expected_key_id:
        return {
            "present": True,
            "valid": False,
            "reason": "public_key_mismatch",
            "key_id": signature.get("key_id"),
            "expected_key_id": expected_key_id,
        }

    try:
        public_key.verify(
            base64.b64decode(
                str(signature["signature_base64"]),
                validate=True,
            ),
            _signature_message(digest),
        )
    except Exception:
        return {
            "present": True,
            "valid": False,
            "reason": "signature_verification_failed",
            "key_id": expected_key_id,
        }

    return {
        "present": True,
        "valid": True,
        "reason": "verified",
        "key_id": expected_key_id,
        "algorithm": "ed25519",
    }
