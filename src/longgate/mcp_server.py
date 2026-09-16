from __future__ import annotations

import os
from pathlib import Path

from . import __version__
from .agent_boundary import SafeWorkspace


def _workspace() -> SafeWorkspace:
    raw = os.environ.get("LONGGATE_SAFE_WORKSPACE")
    if not raw:
        raise RuntimeError("LONGGATE_SAFE_WORKSPACE must point to an approved egress directory.")
    return SafeWorkspace(Path(raw))


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
        }

    @mcp.tool
    def list_safe_files() -> list[str]:
        """List files in the approved egress workspace."""
        return _workspace().list_files()

    @mcp.tool
    def read_safe_text(relative_path: str) -> str:
        """Read one UTF-8 text artifact from the approved egress workspace."""
        return _workspace().read_text(relative_path)

    mcp.run()


if __name__ == "__main__":
    main()
