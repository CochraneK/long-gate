import json
from pathlib import Path

from longgate.provenance import (
    build_provenance,
    verify_provenance,
)


def test_provenance_detects_tampering(tmp_path: Path):
    (tmp_path / "manifest.json").write_text(
        '{"ok": true}',
        encoding="utf-8",
    )
    build_provenance(tmp_path)
    assert verify_provenance(tmp_path)["valid"] is True

    (tmp_path / "manifest.json").write_text(
        '{"ok": false}',
        encoding="utf-8",
    )
    result = verify_provenance(tmp_path)
    assert result["valid"] is False
    assert result["mismatches"][0]["reason"] == "sha256_mismatch"


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
