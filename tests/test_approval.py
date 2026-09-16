from pathlib import Path

import json
import pytest

from longgate.agent_boundary import ApprovedWorkspace
from longgate.approval import ApprovalError, issue_approval, read_approvals


def test_approval_is_bound_to_path_hash_and_purpose(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    artifact = safe / "safe.json"
    artifact.write_text('{"n": 10}', encoding="utf-8")
    ledger = tmp_path / "approvals.jsonl"

    record = issue_approval(
        safe,
        "safe.json",
        ledger,
        "interpret aggregate statistics",
    )

    assert record.relative_path == "safe.json"
    assert len(record.sha256) == 64
    assert read_approvals(ledger)[0].approval_id == record.approval_id

    workspace = ApprovedWorkspace(safe, ledger)
    assert workspace.list_files("interpret aggregate statistics") == ["safe.json"]
    assert workspace.read_text(
        "safe.json",
        "interpret aggregate statistics",
    ) == '{"n": 10}'


def test_wrong_purpose_is_denied(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    (safe / "safe.json").write_text("{}", encoding="utf-8")
    ledger = tmp_path / "approvals.jsonl"
    issue_approval(safe, "safe.json", ledger, "purpose-a")

    workspace = ApprovedWorkspace(safe, ledger)
    with pytest.raises(ApprovalError):
        workspace.read_text("safe.json", "purpose-b")


def test_content_change_invalidates_approval(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    artifact = safe / "safe.json"
    artifact.write_text('{"n": 10}', encoding="utf-8")
    ledger = tmp_path / "approvals.jsonl"
    issue_approval(safe, "safe.json", ledger, "analysis")

    artifact.write_text('{"n": 11}', encoding="utf-8")
    workspace = ApprovedWorkspace(safe, ledger)

    assert workspace.list_files("analysis") == []
    with pytest.raises(ApprovalError):
        workspace.read_text("safe.json", "analysis")


def test_access_log_records_decision_without_payload(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    artifact = safe / "safe.json"
    artifact.write_text('{"secret-ish-content": "not logged"}', encoding="utf-8")
    ledger = tmp_path / "approvals.jsonl"
    access_log = tmp_path / "access.jsonl"
    issue_approval(safe, "safe.json", ledger, "analysis")

    workspace = ApprovedWorkspace(safe, ledger, access_log)
    workspace.read_text("safe.json", "analysis")

    line = access_log.read_text(encoding="utf-8").strip()
    event = json.loads(line)
    assert event["allowed"] is True
    assert event["relative_path"] == "safe.json"
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
