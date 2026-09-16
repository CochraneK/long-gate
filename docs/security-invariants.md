# Security invariants

These are executable product requirements, not documentation-only promises.

1. Raw row-level data is never network eligible.
2. Pseudonymized row-level data is never network eligible.
3. Unknown purposes default to BLOCK.
4. Direct identifiers are excluded from synthetic-model training by supported adapters.
5. Identifier columns are excluded from released exact-statistical summaries.
6. Small groups are suppressed from released group summaries.
7. Synthetic rows require privacy audit and policy evaluation.
8. A policy-approved outbound payload receives a final value-level PII rescan.
9. Any final-scan PII hit blocks payload creation.
10. Aggregate outputs receive their own PII guard.
11. Trust Reports contain counts, metadata, hashes, and decisions — never source row values.
12. The hardened local worker has source-data access and no network.
13. A network worker may have network access but must never mount source-data paths.
14. SafeWorkspace rejects absolute paths and path traversal outside the approved root.
15. Free-text inspection/redaction is local-only until semantic privacy validation exists.
16. No `--force-release` escape hatch is provided.
17. Benchmark fixtures committed to the repository must be synthetic.
18. Semantic preview output remains local-only regardless of detector/audit results.
19. The built-in local LLM path accepts a local model file, not a remote endpoint.
20. Semantic transformation does not grant network-egress permission.
21. Model installation is a separate network-enabled setup capability and accepts no private-data path.
22. Hardened model setup workers mount the Model Vault but not the private-data directory.
23. Private semantic processing resolves local Model Vault files and does not download models.

CI should fail when tests covering these invariants fail.

## Why fail-closed?

Privacy tooling is often uncertain precisely where a user most needs it. Long Gate therefore treats missing capability, unknown purpose, scanner failure, policy ambiguity, or unsupported modality as reasons to stop — not reasons to silently lower the bar.
