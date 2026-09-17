# Research questions

These questions define the current Long Gate paper direction. They should be treated as a working protocol, not retrofitted after seeing final results.

## RQ1 — Release-boundary security

**Does capability-separated release control reduce unauthorized exposure of raw or insufficiently minimized private data compared with pipelines that rely on application-layer instructions or direct agent access?**

Primary evidence:

- raw/pseudonymized data exposure attempts;
- arbitrary-file approval attempts;
- post-approval mutation / TOCTOU attempts;
- path and symlink escape attempts;
- purpose mismatch attempts;
- rate of unsafe artifacts that reach the network-facing boundary.

Core property under test:

```text
No execution principal should simultaneously possess
READ(raw_private_data) + UNRESTRICTED_NETWORK.
```

## RQ2 — Semantic privacy/utility trade-off

**How does Long Gate's local semantic de-identification pipeline compare with simpler baselines on privacy leakage and retained analytical/semantic utility?**

Required comparison family:

- deterministic PII removal only;
- NER/Presidio-style de-identification where applicable;
- one-pass local LLM transformation;
- deterministic + local LLM;
- + independent privacy audit;
- + bounded remediation;
- full Long Gate local semantic pipeline.

Privacy metrics and utility metrics must be reported together. Better privacy obtained only by destroying the task-relevant content is not sufficient evidence.

## RQ3 — Value of bounded remediation

**When the first semantic transformation fails mechanical privacy checks, how often does failure-guided bounded remediation improve privacy evidence, what utility does it cost, and what runtime does it add?**

Compare round 1 with subsequent bounded rounds. Report both successful remediation and cases that remain `LOCAL_ONLY`; do not silently drop failures.

## RQ4 — Robustness to semantic re-identification attacks

**How robust are released/local review candidates to attacks not captured by direct PII removal?**

Attack families should include:

- rare-event leakage;
- relationship leakage;
- combination uniqueness;
- auxiliary-data linkage;
- distinctive phrase copying;
- exact numeric/date reuse;
- malicious/instruction-like content embedded in source documents.

## RQ5 — Systems cost

**What latency, memory, and throughput costs are introduced by Long Gate's capability separation, auditing, and remediation, and how do these costs vary across local model tiers and hardware?**

Report:

- wall-clock latency;
- peak/observed memory where measurable;
- input/output size;
- number of remediation rounds;
- model tier;
- hardware profile;
- privacy/utility outcome.

## Claim discipline

A paper claim should map to at least one pre-declared metric and one reproducible experiment. The repository should not convert engineering properties (for example, "CI is green") into scientific conclusions (for example, "the system is secure") without an explicit experiment or argument.
