from pathlib import Path

import json
import pytest

from longgate.agent_boundary import ApprovedWorkspace
from longgate.approval import ApprovalError, issue_approval, read_approvals
from longgate.egress import stage_json_egress
from longgate.policy import PolicyDecision
from longgate.types import ReleaseClass


def _stage_eligible(
    tmp_path: Path,
    payload: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    decision = PolicyDecision(
        True,
        ReleaseClass.AGGREGATE,
        "test aggregate allow",
    )
    artifact, scan = stage_json_egress(
        payload or {"n_bucket": "10-19", "mean": 2.5},
        tmp_path,
        decision,
    )
    assert scan["passed"] is True
    assert artifact is not None
    return artifact.parent, artifact


def test_approval_is_bound_to_path_hash_and_purpose(tmp_path: Path):
    safe, artifact = _stage_eligible(tmp_path)
    ledger = tmp_path / "approvals.jsonl"

    record = issue_approval(
        safe,
        artifact.name,
        ledger,
        "interpret aggregate statistics",
    )

    assert record.relative_path == artifact.name
    assert record.egress_manifest == "aggregate_egress_manifest.json"
    assert len(record.sha256) == 64
    assert read_approvals(ledger)[0].approval_id == record.approval_id

    workspace = ApprovedWorkspace(safe, ledger)
    assert workspace.list_files("interpret aggregate statistics") == [artifact.name]
    assert workspace.read_text(
        artifact.name,
        "interpret aggregate statistics",
    ) == artifact.read_text(encoding="utf-8")


def test_arbitrary_safe_workspace_file_cannot_be_approved(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    artifact = safe / "copied-in.json"
    artifact.write_text('{"looks": "safe"}', encoding="utf-8")

    with pytest.raises(ApprovalError, match="policy-approved"):
        issue_approval(
            safe,
            artifact.name,
            tmp_path / "approvals.jsonl",
            "analysis",
        )


def test_manifest_hash_must_match_artifact_at_approval_time(tmp_path: Path):
    safe, artifact = _stage_eligible(tmp_path)
    artifact.write_text('{"n_bucket": "changed"}', encoding="utf-8")

    with pytest.raises(ApprovalError, match="policy-approved"):
        issue_approval(
            safe,
            artifact.name,
            tmp_path / "approvals.jsonl",
            "analysis",
        )


def test_wrong_purpose_is_denied(tmp_path: Path):
    safe, artifact = _stage_eligible(tmp_path)
    ledger = tmp_path / "approvals.jsonl"
    issue_approval(safe, artifact.name, ledger, "purpose-a")

    workspace = ApprovedWorkspace(safe, ledger)
    with pytest.raises(ApprovalError):
        workspace.read_text(artifact.name, "purpose-b")


def test_content_change_invalidates_approval(tmp_path: Path):
    safe, artifact = _stage_eligible(tmp_path)
    ledger = tmp_path / "approvals.jsonl"
    issue_approval(safe, artifact.name, ledger, "analysis")

    artifact.write_text('{"n_bucket": "changed"}', encoding="utf-8")
    workspace = ApprovedWorkspace(safe, ledger)

    assert workspace.list_files("analysis") == []
    with pytest.raises(ApprovalError):
        workspace.read_text(artifact.name, "analysis")


def test_approved_read_hashes_and_returns_the_same_bytes(
    monkeypatch,
    tmp_path: Path,
):
    safe, artifact = _stage_eligible(tmp_path)
    approved = artifact.read_bytes()
    ledger = tmp_path / "approvals.jsonl"
    issue_approval(safe, artifact.name, ledger, "analysis")

    original_read_bytes = Path.read_bytes
    artifact_reads = 0

    def racing_read_bytes(path: Path) -> bytes:
        nonlocal artifact_reads
        if path.resolve() == artifact.resolve():
            artifact_reads += 1
            if artifact_reads == 1:
                return approved
            return b'{"n": 999, "secret": "changed-after-check"}'
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", racing_read_bytes)
    workspace = ApprovedWorkspace(safe, ledger)

    assert workspace.read_text(
        artifact.name,
        "analysis",
    ) == approved.decode("utf-8")
    assert artifact_reads == 1


def test_access_log_records_decision_without_payload(tmp_path: Path):
    safe, artifact = _stage_eligible(
        tmp_path,
        {"summary": "secret-ish-content", "n_bucket": "10-19"},
    )
    ledger = tmp_path / "approvals.jsonl"
    access_log = tmp_path / "access.jsonl"
    issue_approval(safe, artifact.name, ledger, "analysis")

    workspace = ApprovedWorkspace(safe, ledger, access_log)
    workspace.read_text(artifact.name, "analysis")

    line = access_log.read_text(encoding="utf-8").strip()
    event = json.loads(line)
    assert event["allowed"] is True
    assert event["relative_path"] == artifact.name
    assert "secret-ish-content" not in line


def test_approval_path_cannot_escape_workspace(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    outside = tmp_path / "raw.txt"
    outside.write_text("private", encoding="utf-8")
    with pytest.raises(ApprovalError):
        issue_approval(
            safe,
            "../raw.txt",
            tmp_path / "approvals.jsonl",
            "analysis",
        )
