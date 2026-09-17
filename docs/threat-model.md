# Threat model

Long Gate is intended to reduce accidental or agent-driven disclosure of sensitive local data to networked AI services.

## In scope

- accidental upload of raw structured data;
- deterministic pseudonym mappings that permit frequency/linkage attacks;
- source identifier reuse in synthetic outputs;
- exact row copying;
- near-copy risk in numeric feature space;
- free-text leakage in a structured-data pipeline;
- cloud agents obtaining broad filesystem access;
- hidden egress caused by an overly permissive pipeline.

## Out of scope in v0.2

- a compromised host OS or administrator account;
- side-channel attacks against the local machine;
- formal differential-privacy guarantees from the Long Gate orchestration layer itself;
- a malicious third-party synthetic backend;
- semantic privacy guarantees for free text, images, audio, or PDFs;
- legal/compliance certification.

## Security posture

The policy is **deny by default**. A failure in inspection, synthesis, audit, or policy evaluation must prevent release.

The strongest deployment pattern is process/container separation:

- local worker: source-data mount, no network;
- cloud worker: network, safe-workspace mount only;
- no service receives both capabilities.
