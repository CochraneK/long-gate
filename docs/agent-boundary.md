# Agent boundary

Long Gate's network agent is a capability-limited consumer, not a general process with access to the research filesystem.

## Filesystem contract

The future network agent receives only an egress workspace:

```text
/private                 local worker only
/runs/<run>/safe         local worker only
/runs/<run>/egress       eligible for network worker mount
```

The Python `SafeWorkspace` class rejects:

- absolute paths;
- `../` traversal;
- resolved paths that escape the safe root, including symlink escapes.

The hardened Compose example enforces the same concept at process/container level. The cloud worker has no `/private` mount.

## Network contract

The local worker is configured with `network_mode: none`.

The future cloud worker may have network access, but it receives only a read-only `/safe` mount. This is deliberately stronger than giving a cloud agent access to the whole filesystem and asking it not to inspect private files.

## Current release posture

Long Gate v0.2 does not make cloud API calls. The cloud-worker entry in the hardened Compose file is a mount-boundary demonstration only.


## MCP surface

Install the optional server:

```bash
pip install 'long-gate[mcp]'
export LONGGATE_SAFE_WORKSPACE=/path/to/approved/egress
longgate-mcp
```

The network-facing MCP server intentionally exposes only:

- `gate_info`
- `list_safe_files`
- `read_safe_text(relative_path)`

It does not expose a raw-path parameter, arbitrary shell execution, arbitrary Python execution, or source-data mounts.
