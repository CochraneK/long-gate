# Evaluation protocol

This document is the working experimental protocol for a Long Gate systems/security paper. It is intentionally stricter than the engineering benchmark suite.

## 1. Unit of analysis

Every experimental run is identified by:

- Long Gate commit SHA;
- experiment ID;
- dataset/version;
- baseline or ablation variant;
- model identity and immutable model hash where applicable;
- seed;
- hardware/environment metadata;
- configuration SHA-256.

Results missing these fields should not be used in final paper tables unless the omission is explicitly justified.

## 2. Dataset discipline

Datasets are divided conceptually into:

1. **development fixtures** — synthetic/small data used for debugging and CI;
2. **public evaluation datasets** — fixed third-party datasets used for main results;
3. **red-team corpora** — controlled attack cases designed to stress rare-event, linkage, relationship, and prompt-injection-style leakage.

Development fixtures must not be reported as if they were independent test evidence.

Third-party datasets must have a provenance note containing source, version/date, license/terms, preprocessing, and checksums where redistribution permits.

## 3. Baseline discipline

Baselines should be implemented through the same experiment interface and evaluated on the same input subset and metric code where possible.

Semantic evaluation should include at least:

- B1 deterministic PII removal;
- B2 NER/Presidio-style de-identification where supported;
- B3 one-pass local LLM;
- B4 deterministic + local LLM;
- B5 B4 + independent audit;
- B6 B5 + bounded remediation;
- B7 full Long Gate release-boundary workflow where applicable.

If a baseline cannot satisfy an experiment's threat model, report that mismatch instead of silently omitting it.

## 4. Repetition and seeds

The smoke configuration is infrastructure-only. Main paper experiments should use a frozen seed list before final analysis.

For stochastic components, report all declared seeds/runs, including failures. Do not rerun only unfavorable outcomes unless a documented infrastructure error occurred.

Model decoding settings must be frozen in the experiment configuration.

## 5. Privacy metrics

Metric families may include:

- direct PII leakage count/rate;
- exact number/date reuse;
- n-gram/source-copy reuse;
- distinctive-token reuse;
- rare-event attack success;
- relationship inference success;
- auxiliary-data linkage/re-identification success;
- unsafe-egress success rate for release-boundary attacks.

Mechanical metrics are evidence, not proof of anonymity.

## 6. Utility metrics

Privacy results must be paired with utility evidence appropriate to the dataset/task. Candidate metrics include:

- semantic/task-label preservation;
- downstream classification/regression performance;
- factual/relationship retention required by the intended task;
- human or blinded rubric evaluation where automated metrics are inadequate.

The final metric set should be frozen before the main evaluation.

## 7. Ablations

At minimum, test removal of:

- deterministic pre-scrub;
- independent audit;
- failure-guided remediation;
- purpose-bound approval;
- hash-bound egress manifest;
- narrow SafeWorkspace/MCP boundary where the experiment concerns release control.

An ablation must change one declared mechanism at a time unless explicitly testing interactions.

## 8. Statistical reporting

The artifact pipeline may compute descriptive mean, sample standard deviation, and an approximate 95% normal confidence interval for repeated numeric measurements. The paper must not imply that repeated seeds are independent samples from a population when they are not.

Where hypothesis testing is used, the test and correction strategy should be declared before final analysis and matched to the experimental unit.

## 9. Failure reporting

Report:

- crashes/timeouts;
- model load failures;
- `LOCAL_ONLY` outcomes;
- failed remediation rounds;
- unavailable baselines;
- missing hardware measurements.

Do not exclude these from denominators without an explicit reason.

## 10. Artifact freeze

Before submission/artifact review:

1. freeze the evaluation commit/tag;
2. freeze public-dataset versions/checksums;
3. freeze model files/revisions/checksums;
4. export the exact experiment configs;
5. archive raw normalized result records;
6. regenerate every paper table/figure from those records;
7. produce an anonymized artifact copy if the venue requires anonymous review.
