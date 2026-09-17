# Agent boundary

Long Gate's network agent is a capability-limited consumer, not a general process with access to the research filesystem.

## Filesystem contract

The network agent receives only an egress workspace **and must also present an exact declared purpose that matches a local hash-bound approval**:

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

The network worker may have network access, but it receives only a read-only safe workspace. This is deliberately stronger than giving a cloud agent access to the whole filesystem and asking it not to inspect private files.

## Current release posture

Long Gate v0.2 does not itself make cloud API calls. The cloud-worker entry in the hardened Compose file demonstrates the capability boundary for an MCP/network consumer.

Row-level synthetic release remains hard-locked in the current pre-1.0 baseline. The normal network-readable artifact is therefore a disclosure-limited aggregate that survived the release pipeline.

## Eligibility before approval

A file does not become network-readable merely by appearing in the safe workspace.

Before `approve-egress` records an approval, Long Gate requires a matching versioned egress manifest proving:

- policy `allow = true`;
- final scan passed;
- currently allowed aggregate release class;
- exact artifact filename;
- exact artifact SHA-256.

Only then can a local actor bind that artifact to an explicit purpose.

This protects the user from accidentally copying an arbitrary file into `egress/` and approving it as though Long Gate had cleared it.

## MCP surface

Install the optional server:

```bash
pip install 'long-gate[mcp]'
export LONGGATE_SAFE_WORKSPACE=/path/to/approved/egress
export LONGGATE_APPROVAL_LEDGER=/path/to/approvals.jsonl
export LONGGATE_ACCESS_LOG=/path/to/access.jsonl
longgate-mcp
```

The network-facing MCP server intentionally exposes only:

- `gate_info`
- `list_safe_files(purpose)`
- `read_safe_text(relative_path, purpose)`

Artifact access requires `LONGGATE_APPROVAL_LEDGER`. The server has no tool for creating approvals.

An allowed read hashes and returns the same byte snapshot, so content cannot be swapped between authorization and return.

The server does not expose:

- a raw-path parameter;
- arbitrary shell execution;
- arbitrary Python execution;
- source-data mounts;
- an approval-creation tool;
- a force-release escape hatch.

See [Egress approval ledger](approval-ledger.md) for the manifest + path + SHA-256 + purpose authorization layer and access logging.
