# Security invariants

These rules are treated as executable product requirements, not documentation-only promises.

1. Raw row-level data is never network eligible.
2. Pseudonymized row-level data is never network eligible.
3. Unknown purposes default to BLOCK.
4. Direct identifiers are excluded from synthetic-model training by supported production adapters.
5. Identifier columns are excluded from released exact-statistical summaries.
6. Small groups are suppressed from released group summaries.
7. Synthetic rows require a privacy audit before policy evaluation can allow them.
8. A policy-approved payload receives a final value-level PII rescan before staging.
9. Any final-scan PII hit blocks payload creation.
10. Trust Reports contain counts, metadata, hashes, and decisions — never source row values.
11. The hardened local worker has source-data access and no network.
12. A future network worker may have network access but must never mount source-data paths.
13. No `--force-release` escape hatch is provided.

CI must fail when tests covering these invariants fail.
