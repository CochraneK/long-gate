# Egress approval ledger

Long Gate separates **artifact eligibility** from **network-agent authorization**.

A network-facing AI should not be able to read a file merely because somebody copied it into an `egress/` directory. The local approval step therefore verifies both the Long Gate release decision and the exact bytes being approved.

## Two gates, not one

```text
Long Gate release pipeline
        ↓
versioned egress manifest says the artifact is eligible
        ↓
local actor approves one exact artifact for one exact purpose
        ↓
network MCP may read it
```

Passing the privacy/release gate is necessary but not sufficient for network access.

## Egress-manifest binding

When Long Gate stages an allowed egress artifact, it writes a versioned manifest containing:

- policy decision;
- release class;
- final-scan result;
- exact artifact filename;
- exact artifact SHA-256.

For example:

```text
longgate-runs/LG-123/egress/
├── aggregate_egress_manifest.json
└── safe_aggregate.json
```

`approve-egress` refuses the artifact unless the matching manifest records:

```text
format = long-gate-egress-manifest-v1
allow = true
allow_after_final_scan = true
release_class = aggregate
final_scan.passed = true
artifact = exact current filename
artifact_sha256 = exact current SHA-256
```

In the current pre-1.0 posture, row-level synthetic release remains hard-locked, so the normal approvable artifact is a disclosure-limited aggregate.

Copying an arbitrary file into the safe workspace does **not** make it approvable.

## Approval binding

After the manifest check succeeds, each approval is bound to:

```text
manifest-backed eligibility
+ relative path
+ SHA-256
+ exact purpose
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
- exact declared purpose;
- the matching egress-manifest path.

It does not contain artifact content.

## What happens if somebody edits the artifact?

Suppose `safe_aggregate.json` is approved and then changed.

The old approval remains in the ledger as historical metadata, but the network-side read recomputes the SHA-256 of the exact byte snapshot being returned. Because the digest no longer matches the approval, access is denied.

The read path hashes and returns the **same byte snapshot**, avoiding a check-then-reopen race.

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

The network process therefore cannot make a new file readable by approving it itself.

## Access log

Allowed and denied reads can be appended to a local access log containing:

- timestamp;
- relative path;
- purpose;
- artifact SHA-256 when available;
- allow/deny;
- reason or approval ID.

The access log does not contain artifact content.

This log is observational, not a cryptographic append-only log or signature. Provenance signing is handled separately.

## Hardened deployment

The hardened Compose example mounts:

- `/safe` read-only;
- `/policy/approvals.jsonl` read-only;
- `/access` writable for access events;
- **no `/private` mount** on the network worker.

The local/private worker has `network_mode: none`.

This means the network process cannot:

- read the raw-data mount;
- create an approval through MCP;
- mutate the safe workspace;
- keep reading an artifact after its approved hash no longer matches.

See [Agent boundary](agent-boundary.md) and [Security invariants](security-invariants.md).
