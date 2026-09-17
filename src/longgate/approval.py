from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .egress import EGRESS_MANIFEST_FORMAT
from .utils import sha256_file, utc_now


class ApprovalError(PermissionError):
    pass


def _safe_relative(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    rel = Path(relative)
    if rel.is_absolute():
        raise ApprovalError("Approval paths must be relative to the safe workspace.")
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ApprovalError("Approval path escapes the safe workspace.") from exc
    if not candidate.is_file():
        raise FileNotFoundError(relative)
    return candidate


def _eligible_egress_manifest(
    root: Path,
    artifact: Path,
) -> tuple[str, str]:
    """Require a matching Long Gate egress manifest before local approval.

    The manifest must name the exact artifact, bind its SHA-256, record a
    successful final scan, and represent a policy-allowed aggregate release.
    This keeps the approval command from turning an arbitrary file copied into
    the safe workspace into a network-readable artifact.
    """
    digest = sha256_file(artifact)
    for manifest in sorted(artifact.parent.glob("*egress_manifest.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeError):
            continue
        final_scan = data.get("final_scan")
        if (
            data.get("format") == EGRESS_MANIFEST_FORMAT
            and data.get("artifact") == artifact.name
            and data.get("artifact_sha256") == digest
            and data.get("allow") is True
            and data.get("allow_after_final_scan") is True
            and data.get("release_class") == "aggregate"
            and isinstance(final_scan, dict)
            and final_scan.get("passed") is True
        ):
            return str(manifest.resolve().relative_to(root)), digest

    raise ApprovalError(
        "Artifact is not backed by a matching policy-approved Long Gate "
        "egress manifest. Run the Long Gate release pipeline first; do not "
        "copy arbitrary files into the safe workspace."
    )


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    created_at: str
    relative_path: str
    sha256: str
    purpose: str
    egress_manifest: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AccessEvent:
    time: str
    relative_path: str
    purpose: str
    sha256: str | None
    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def issue_approval(
    workspace: str | Path,
    relative_path: str | Path,
    ledger_path: str | Path,
    purpose: str,
) -> ApprovalRecord:
    purpose = purpose.strip()
    if not purpose:
        raise ValueError("Approval purpose must be non-empty.")

    root = Path(workspace).expanduser().resolve()
    artifact = _safe_relative(root, relative_path)
    manifest_relative, digest = _eligible_egress_manifest(
        root,
        artifact,
    )
    record = ApprovalRecord(
        approval_id=f"LGA-{uuid.uuid4().hex[:16]}",
        created_at=utc_now(),
        relative_path=str(artifact.relative_to(root)),
        sha256=digest,
        purpose=purpose,
        egress_manifest=manifest_relative,
    )
    ledger = Path(ledger_path).expanduser().resolve()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                record.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
    return record


def read_approvals(path: str | Path) -> list[ApprovalRecord]:
    ledger = Path(path).expanduser().resolve()
    if not ledger.is_file():
        return []
    records: list[ApprovalRecord] = []
    for line_no, line in enumerate(
        ledger.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            records.append(ApprovalRecord(**data))
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(
                f"Invalid approval ledger record at line {line_no}."
            ) from exc
    return records


def matching_approval_digest(
    relative_path: str,
    digest: str,
    ledger_path: str | Path,
    purpose: str,
) -> ApprovalRecord | None:
    """Match an approval against a digest already computed from the bytes in use.

    Callers that expose file content across a trust boundary should read the
    artifact once, hash those exact bytes, and use this helper. That avoids a
    check-then-reopen window where the file could change after authorization.
    """
    for record in reversed(read_approvals(ledger_path)):
        if (
            record.relative_path == relative_path
            and record.sha256 == digest
            and record.purpose == purpose
        ):
            return record
    return None


def matching_approval(
    workspace: str | Path,
    relative_path: str | Path,
    ledger_path: str | Path,
    purpose: str,
) -> ApprovalRecord | None:
    root = Path(workspace).expanduser().resolve()
    artifact = _safe_relative(root, relative_path)
    relative = str(artifact.relative_to(root))
    digest = sha256_file(artifact)
    return matching_approval_digest(
        relative,
        digest,
        ledger_path,
        purpose,
    )


def list_approved_files(
    workspace: str | Path,
    ledger_path: str | Path,
    purpose: str,
) -> list[str]:
    root = Path(workspace).expanduser().resolve()
    files: list[str] = []
    seen: set[str] = set()
    for record in reversed(read_approvals(ledger_path)):
        if record.purpose != purpose or record.relative_path in seen:
            continue
        seen.add(record.relative_path)
        try:
            artifact = _safe_relative(root, record.relative_path)
        except (ApprovalError, FileNotFoundError):
            continue
        if sha256_file(artifact) == record.sha256:
            files.append(record.relative_path)
    return sorted(files)


def append_access_event(
    path: str | Path | None,
    event: AccessEvent,
) -> None:
    if path is None:
        return
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                event.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
