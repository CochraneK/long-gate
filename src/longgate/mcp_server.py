from __future__ import annotations

import os
from pathlib import Path

from . import __version__
from .agent_boundary import ApprovedWorkspace


def _workspace() -> ApprovedWorkspace:
    raw = os.environ.get("LONGGATE_SAFE_WORKSPACE")
    ledger = os.environ.get("LONGGATE_APPROVAL_LEDGER")
    access_log = os.environ.get("LONGGATE_ACCESS_LOG")
    if not raw:
        raise RuntimeError(
            "LONGGATE_SAFE_WORKSPACE must point to an egress directory."
        )
    if not ledger:
        raise RuntimeError(
            "LONGGATE_APPROVAL_LEDGER is required; "
            "network-facing reads fail closed without local approvals."
        )
    return ApprovedWorkspace(
        Path(raw),
        Path(ledger),
        Path(access_log) if access_log else None,
    )


def main() -> None:
    try:
        from fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "MCP server requires the optional dependency: pip install 'long-gate[mcp]'"
        ) from exc

    mcp = FastMCP(
        "Long Gate",
        instructions=(
            "This server exposes only policy-approved artifacts from a safe workspace. "
            "It has no tool for raw/private filesystem access."
        ),
    )

    @mcp.tool
    def gate_info() -> dict[str, object]:
        """Return non-sensitive capability information."""
        return {
            "name": "Long Gate",
            "version": __version__,
            "raw_filesystem_access": False,
            "workspace": "egress-only",
            "approval_required": True,
            "approval_binding": "relative_path + sha256 + purpose",
        }

    @mcp.tool
    def list_safe_files(purpose: str) -> list[str]:
        """List only artifacts approved for the declared purpose."""
        return _workspace().list_files(purpose)

    @mcp.tool
    def read_safe_text(relative_path: str, purpose: str) -> str:
        """Read one hash-bound artifact approved for the declared purpose."""
        return _workspace().read_text(
            relative_path,
            purpose,
        )

    mcp.run()


if __name__ == "__main__":
    main()
