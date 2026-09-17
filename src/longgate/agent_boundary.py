from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .approval import (
    AccessEvent,
    ApprovalError,
    append_access_event,
    list_approved_files,
    matching_approval_digest,
)
from .utils import utc_now


class WorkspaceViolation(PermissionError):
    pass


@dataclass(frozen=True)
class SafeWorkspace:
    """Filesystem capability exposed to a future network agent.

    The network agent receives this root, not the source-data root.
    """

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())

    def _resolve(self, relative: str | Path) -> Path:
        rel = Path(relative)
        if rel.is_absolute():
            raise WorkspaceViolation("Absolute paths are not allowed.")
        candidate = (self.root / rel).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceViolation("Path escapes the safe workspace.") from exc
        return candidate

    def list_files(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*") if p.is_file())

    def read_text(self, relative: str | Path) -> str:
        path = self._resolve(relative)
        if not path.is_file():
            raise FileNotFoundError(relative)
        return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class ApprovedWorkspace:
    """Read capability limited by path, exact content hash, and declared purpose."""

    root: Path
    approval_ledger: Path
    access_log: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())
        object.__setattr__(
            self,
            "approval_ledger",
            self.approval_ledger.resolve(),
        )
        if self.access_log is not None:
            object.__setattr__(
                self,
                "access_log",
                self.access_log.resolve(),
            )

    def list_files(self, purpose: str) -> list[str]:
        purpose = purpose.strip()
        if not purpose:
            raise ApprovalError("Purpose is required.")
        return list_approved_files(
            self.root,
            self.approval_ledger,
            purpose,
        )

    def read_text(
        self,
        relative: str | Path,
        purpose: str,
    ) -> str:
        purpose = purpose.strip()
        if not purpose:
            raise ApprovalError("Purpose is required.")

        workspace = SafeWorkspace(self.root)
        try:
            resolved = workspace._resolve(relative)
            if not resolved.is_file():
                raise FileNotFoundError(relative)
            relative_name = str(resolved.relative_to(self.root))
            payload = resolved.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            record = matching_approval_digest(
                relative_name,
                digest,
                self.approval_ledger,
                purpose,
            )
        except (WorkspaceViolation, ApprovalError, FileNotFoundError) as exc:
            append_access_event(
                self.access_log,
                AccessEvent(
                    time=utc_now(),
                    relative_path=str(relative),
                    purpose=purpose,
                    sha256=None,
                    allowed=False,
                    reason=str(exc),
                ),
            )
            raise

        if record is None:
            append_access_event(
                self.access_log,
                AccessEvent(
                    time=utc_now(),
                    relative_path=str(relative),
                    purpose=purpose,
                    sha256=digest,
                    allowed=False,
                    reason=(
                        "No hash-bound approval exists for "
                        "these exact bytes and purpose."
                    ),
                ),
            )
            raise ApprovalError(
                "Artifact is not approved for this purpose "
                "or its content changed after approval."
            )

        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            append_access_event(
                self.access_log,
                AccessEvent(
                    time=utc_now(),
                    relative_path=str(relative),
                    purpose=purpose,
                    sha256=digest,
                    allowed=False,
                    reason="Approved artifact is not valid UTF-8 text.",
                ),
            )
            raise ValueError("Approved artifact is not valid UTF-8 text.") from exc

        append_access_event(
            self.access_log,
            AccessEvent(
                time=utc_now(),
                relative_path=str(relative),
                purpose=purpose,
                sha256=record.sha256,
                allowed=True,
                reason=f"approval={record.approval_id}",
            ),
        )
        return text
