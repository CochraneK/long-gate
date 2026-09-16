# Egress approval ledger

Long Gate separates **artifact eligibility** from **network-agent authorization**.

An artifact may pass a privacy/release gate and still not be readable by a network-facing AI until a local actor explicitly approves that exact artifact for a declared purpose.

## Approval binding

Each approval is bound to:

```text
relative path + SHA-256 + exact purpose
```

If the file changes, the SHA-256 changes and the approval stops matching.

If the network agent declares a different purpose, the approval does not match.

## Issue an approval locally

Suppose a Long Gate run produced:

```text
longgate-runs/LG-123/egress/safe_aggregate.json
```

Create a local approval:

```bash
longgate approve-egress \
  longgate-runs/LG-123/egress/safe_aggregate.json \
  --workspace longgate-runs/LG-123/egress \
  --ledger ./longgate-policy/approvals.jsonl \
  --purpose "interpret aggregate statistics"
```

The ledger contains metadata only:

- approval ID;
- timestamp;
- relative artifact path;
- artifact SHA-256;
- declared purpose.

It does not contain the artifact contents.

## Network-facing MCP

The MCP server requires:

```bash
export LONGGATE_SAFE_WORKSPACE=/path/to/egress
export LONGGATE_APPROVAL_LEDGER=/path/to/approvals.jsonl
export LONGGATE_ACCESS_LOG=/path/to/access.jsonl
longgate-mcp
```

Its read tools require the purpose explicitly:

```text
list_safe_files(purpose)
read_safe_text(relative_path, purpose)
```

There is intentionally **no MCP tool that creates an approval**.

## Access log

Allowed and denied reads can be appended to a local access log containing:

- timestamp;
- relative path;
- purpose;
- artifact SHA-256 when available;
- allow/deny;
- reason or approval ID.

The access log does not contain artifact content.

This log is observational, not a cryptographic append-only log or signature. Key-backed attestation remains separate future work.

## Hardened deployment

The hardened Compose example mounts:

- `/safe` read-only;
- `/policy/approvals.jsonl` read-only;
- `/access` writable for access events;
- **no `/private` mount** on the network worker.

The local/private worker still has `network_mode: none`.

This means the network process cannot approve a new file through the MCP interface, and changing an already-approved file invalidates its hash binding.
