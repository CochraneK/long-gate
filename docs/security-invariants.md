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
10. Aggregate outputs receive their own PII guard and explicit disclosure-limiting transform before authorization; structured keys and values are both scanned because column names can contain direct identifiers.
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
24. Semantic release evidence may qualify an artifact for manual review but can never auto-authorize network egress.
25. Row-level synthetic production criteria are evidence-only in pre-1.0; even a satisfied checklist returns `release_allowed = false`.
26. A passing synthetic privacy audit is evidence, not authorization; the pre-1.0 PolicyEngine must still deny row-level synthetic release.
27. The release-ladder aggregate fallback must not expose exact extrema or exact sample counts; it buckets counts, rounds continuous summaries, and suppresses columns below the profile minimum N.
28. Image, scanned-PDF OCR, and audio paths are local-only and cannot grant egress permission.
29. Local OCR has no network fallback and returns aggregate PII counts rather than OCR text.
30. Image/OCR processing rejects inputs above the configured pixel safety limit.
31. Deployment validation rejects any service that combines private-data capability with network access.
32. A private-data service may not receive Model Vault write capability or the network-facing safe workspace.
33. Provenance signatures are optional and never cause Long Gate to copy or manage long-lived signing keys.
34. Unsigned provenance may claim integrity consistency only, never authenticated origin or resistance to coordinated artifact + manifest replacement.
35. The Python `LongGate` API is trusted-local. Values returned by `inspect()` or `exact()` are not egress authorizations; network agents consume only approved egress artifacts through the MCP boundary.
36. An approved network-side read hashes and returns the same byte snapshot; approval must never be checked against one file read and content returned from a later reopen.
37. Provenance verification may hash artifacts only inside the selected run directory; absolute paths, parent traversal, and symlink escapes fail closed.
38. Scanned-PDF page dimensions are checked against the pixel limit before allocating or rendering the bitmap.
39. Privacy-boundary Compose services drop all Linux capabilities and enable `no-new-privileges`; deployment validation parses Compose structurally and fails closed on unresolved external `extends`.
40. Every staged egress artifact is bound to a versioned egress manifest containing its exact filename and SHA-256. Local approval requires that manifest, `allow=true`, a successful final scan, and an exact digest match; arbitrary files copied into the safe workspace cannot be approved.
41. Hardware inspection is local-only. Long Gate may read OS/CPU/RAM/disk metadata and, when locally available, query `nvidia-smi`; hardware-detection failure must not trigger a remote fallback or upload hardware inventory.
42. Semantic de-identification remediation is bounded to at most three local model rounds. Failure to satisfy the defined evidence gate ends in `LOCAL_ONLY`, never an unbounded autonomous loop or policy relaxation.
43. A semantic `MANUAL_REVIEW_CANDIDATE` is evidence for local human review only. It always keeps `automatic_release_allowed=false` and `release_allowed=false` in the current baseline.
44. Semantic Trust Reports may contain hashes, local model metadata, risk counts/rates, decisions, and next actions, but must not embed the source narrative or transformed narrative.
45. Deterministic pre-scrubbing and local model transformation are preparation steps, not release authorization. Network egress still requires a separately supported policy and approval path.

CI should fail when tests covering these invariants fail.

## Why fail-closed?

Privacy tooling is often uncertain precisely where a user most needs it. Long Gate therefore treats missing capability, unknown purpose, scanner failure, policy ambiguity, or unsupported modality as reasons to stop — not reasons to silently lower the bar.
