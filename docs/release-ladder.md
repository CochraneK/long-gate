# Release ladder

Long Gate does not treat a blocked representation as the end of the workflow.

The release ladder separates **workflow progress** from **representation permission**:

```text
requested row-level synthetic
        ↓
privacy + policy audit
        ↓
row-level allowed? ── yes ──> staged synthetic artifact
        │
        no
        ↓
safe aggregate fallback
        ↓
aggregate allowed? ── yes ──> staged aggregate artifact
        │
        no
        ↓
LOCAL_ONLY + explicit next actions
```

## Why this matters

A fail-closed system should refuse unsafe disclosure, but it should not strand the user.

Long Gate therefore keeps two ideas separate:

- **row-level release allowed?**
- **can the user's task still continue safely?**

For example, the built-in research profile still disables row-level synthetic egress. A run can nevertheless finish with:

```json
{
  "status": "PASS",
  "release_class": "aggregate",
  "safe_payload": ".../egress/safe_aggregate.json"
}
```

The synthetic table remains local. The aggregate artifact is a different representation that passed its own release path.

The fallback is deliberately **less detailed than the local exact describe result**. Before it can be authorized, Long Gate:

- removes exact minima and maxima;
- replaces exact row/non-missing counts with coarse count buckets;
- rounds released means and standard deviations;
- suppresses numeric columns whose non-missing N is below the active profile's minimum dataset size;
- then runs the aggregate PII guard and final egress scan.

Local exact statistics can remain exact because they stay local. The network-eligible fallback is a separate disclosure-limited representation.

## Machine-readable blockers

Privacy audits include `reason_codes` such as:

- `backend_not_approved`
- `profile_disallows_row_level`
- `exact_row_overlap`
- `identifier_overlap`
- `rare_quasi_overlap`
- `near_copy_rate`
- `free_text_present`

These codes drive remediation guidance. They are not a magic privacy score.

## What Long Gate will not do

The release ladder never:

- flips a privacy profile from blocked to allowed just to make a run green;
- marks an unreviewed synthetic backend as certified;
- silently lowers k/near-copy thresholds;
- treats regex-clean text as semantically anonymous;
- sends a staged artifact to the network.

If neither row-level nor aggregate disclosure is justified, the workflow returns `LOCAL_ONLY` with explicit next actions instead of a misleading PASS.

## Trust Report

The Trust Report records:

- the requested release class;
- the granted release class;
- why row-level release was rejected;
- whether aggregate fallback was used;
- the next remediation actions;
- the final egress scan result.

This keeps fail-closed behavior compatible with a usable workflow.
