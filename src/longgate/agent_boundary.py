from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*")
            if p.is_file()
        )

    def read_text(self, relative: str | Path) -> str:
        path = self._resolve(relative)
        if not path.is_file():
            raise FileNotFoundError(relative)
        return path.read_text(encoding="utf-8")
