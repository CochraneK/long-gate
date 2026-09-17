import hashlib
import json
from pathlib import Path

import pytest

from longgate.provenance import (
    build_provenance,
    sign_provenance,
    verify_provenance,
    verify_provenance_signature,
)


def test_provenance_detects_tampering(tmp_path: Path):
    (tmp_path / "manifest.json").write_text(
        '{"ok": true}',
        encoding="utf-8",
    )
    build_provenance(tmp_path)
    verification = verify_provenance(tmp_path)
    assert verification["valid"] is True
    assert verification["integrity_valid"] is True
    assert verification["authenticated"] is False
    assert verification["verification_scope"] == "integrity_only"
    assert "coordinated artifact + manifest replacement" in verification["note"]

    (tmp_path / "manifest.json").write_text(
        '{"ok": false}',
        encoding="utf-8",
    )
    result = verify_provenance(tmp_path)
    assert result["valid"] is False
    assert result["mismatches"][0]["reason"] == "sha256_mismatch"


def test_provenance_rejects_artifact_path_escape(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("must-not-be-read", encoding="utf-8")

    provenance_path = build_provenance(run)
    document = json.loads(provenance_path.read_text(encoding="utf-8"))
    document["artifacts"][0]["path"] = "../secret.txt"
    core = {
        "format": document["format"],
        "artifacts": document["artifacts"],
    }
    canonical = json.dumps(
        core,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    document["integrity_digest"] = hashlib.sha256(canonical).hexdigest()
    provenance_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = verify_provenance(run)
    assert result["valid"] is False
    assert result["integrity_digest_matches"] is True
    assert result["mismatches"] == [
        {"path": "../secret.txt", "reason": "path_outside_run"}
    ]


def test_provenance_document_does_not_claim_signature(tmp_path: Path):
    (tmp_path / "audit.json").write_text(
        "{}",
        encoding="utf-8",
    )
    path = build_provenance(tmp_path)
    document = json.loads(
        path.read_text(encoding="utf-8")
    )
    assert document["signature"] is None
    assert "not a digital signature" in document["signature_note"]


def _write_signing_keys(tmp_path: Path) -> tuple[Path, Path]:
    serialization = pytest.importorskip(
        "cryptography.hazmat.primitives.serialization"
    )
    ed25519 = pytest.importorskip(
        "cryptography.hazmat.primitives.asymmetric.ed25519"
    )
    key = ed25519.Ed25519PrivateKey.generate()
    private_path = tmp_path / "signing-key.pem"
    public_path = tmp_path / "verification-key.pem"
    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def test_provenance_covers_aggregate_release_artifacts(tmp_path: Path):
    egress = tmp_path / "egress"
    egress.mkdir()
    (egress / "safe_aggregate.json").write_text(
        '{"n": 10}',
        encoding="utf-8",
    )
    (egress / "aggregate_egress_manifest.json").write_text(
        '{"allow": true}',
        encoding="utf-8",
    )
    path = build_provenance(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    covered = {item["path"] for item in document["artifacts"]}
    assert "egress/safe_aggregate.json" in covered
    assert "egress/aggregate_egress_manifest.json" in covered


def test_ed25519_provenance_signature_round_trip(tmp_path: Path):
    (tmp_path / "manifest.json").write_text(
        '{"ok": true}',
        encoding="utf-8",
    )
    build_provenance(tmp_path)
    signing_key, public_key = _write_signing_keys(tmp_path)

    signature_path = sign_provenance(
        tmp_path,
        signing_key,
    )
    assert signature_path.exists()

    signature = verify_provenance_signature(
        tmp_path,
        public_key,
    )
    assert signature["valid"] is True

    combined = verify_provenance(
        tmp_path,
        public_key,
    )
    assert combined["valid"] is True
    assert combined["integrity_valid"] is True
    assert combined["authenticated"] is True
    assert combined["verification_scope"] == "signed_authenticity"
    assert combined["signature"]["valid"] is True


def test_wrong_public_key_rejects_signature(tmp_path: Path):
    (tmp_path / "manifest.json").write_text(
        '{"ok": true}',
        encoding="utf-8",
    )
    build_provenance(tmp_path)
    signing_key, _ = _write_signing_keys(tmp_path)
    sign_provenance(tmp_path, signing_key)

    other_dir = tmp_path / "other"
    other_dir.mkdir()
    _, other_public_key = _write_signing_keys(other_dir)
    result = verify_provenance_signature(
        tmp_path,
        other_public_key,
    )
    assert result["valid"] is False
    assert result["reason"] == "public_key_mismatch"


def test_signing_refuses_tampered_provenance(tmp_path: Path):
    artifact = tmp_path / "manifest.json"
    artifact.write_text('{"ok": true}', encoding="utf-8")
    build_provenance(tmp_path)
    signing_key, _ = _write_signing_keys(tmp_path)

    artifact.write_text('{"ok": false}', encoding="utf-8")
    with pytest.raises(ValueError, match="Refusing to sign"):
        sign_provenance(tmp_path, signing_key)
