from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

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


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    created_at: str
    relative_path: str
    sha256: str
    purpose: str

    def to_dict(self) -> dict[str, str]:
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
    record = ApprovalRecord(
        approval_id=f"LGA-{uuid.uuid4().hex[:16]}",
        created_at=utc_now(),
        relative_path=str(artifact.relative_to(root)),
        sha256=sha256_file(artifact),
        purpose=purpose,
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
    for record in reversed(read_approvals(ledger_path)):
        if (
            record.relative_path == relative
            and record.sha256 == digest
            and record.purpose == purpose
        ):
            return record
    return None


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
