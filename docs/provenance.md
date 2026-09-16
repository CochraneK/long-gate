# Provenance and integrity

Long Gate records SHA-256 hashes for run artifacts so later changes can be detected.

Each structured run writes:

```text
provenance.json
```

Verify it:

```bash
longgate verify-run longgate-runs/LG-...
```

The provenance document covers artifacts such as:
- manifest;
- audit result;
- synthetic preview;
- egress manifest / safe payload when present;
- Trust Report.

## Important distinction

The current baseline is **integrity-verifiable, not digitally signed**.

A SHA-256 manifest can detect post-run modification. It does not authenticate:
- who ran Long Gate;
- which physical machine ran it;
- whether the host was compromised;
- whether a trusted maintainer signed the result.

A future signing layer can add key-backed authenticity without changing the artifact-hashing contract.
