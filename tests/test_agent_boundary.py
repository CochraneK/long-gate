from pathlib import Path

import pytest

from longgate.agent_boundary import SafeWorkspace, WorkspaceViolation


def test_safe_workspace_reads_only_inside_root(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    (safe / "payload.json").write_text("{}", encoding="utf-8")
    ws = SafeWorkspace(safe)
    assert ws.read_text("payload.json") == "{}"


def test_safe_workspace_blocks_parent_escape(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    (tmp_path / "raw.csv").write_text("secret", encoding="utf-8")
    ws = SafeWorkspace(safe)
    with pytest.raises(WorkspaceViolation):
        ws.read_text("../raw.csv")


def test_safe_workspace_blocks_absolute_path(tmp_path: Path):
    safe = tmp_path / "egress"
    safe.mkdir()
    ws = SafeWorkspace(safe)
    with pytest.raises(WorkspaceViolation):
        ws.read_text(Path("/etc/passwd"))


def test_public_python_api_declares_trusted_local_boundary():
    from longgate import LongGate

    doc = (LongGate.__doc__ or "").lower()
    assert "trusted-local" in doc
    assert "not" in doc and "egress" in doc
    assert "safeworkspace/mcp" in doc
