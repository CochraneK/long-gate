# Long Gate research artifact

This directory is the **paper-evidence layer** for Long Gate. The product runtime lives in `src/longgate/`; engineering regression tests live in `tests/` and `benchmarks/`. Research code here exists to make scientific claims reproducible.

The separation is deliberate:

```text
src/ + tests/ + benchmarks/   -> is the software behaving as intended?
research/                     -> do the paper's empirical claims hold?
```

## Integrity rule

`make research-smoke` is a CI-safe artifact-pipeline and synthetic red-team smoke test. It is **not paper evidence** and must never be cited as a completed experiment.

A future `research-paper` target should only be added after the paper protocol, public datasets, baselines, metrics, local-model revisions, and main experiment configuration are frozen.

## Current research questions

See [`research-questions.md`](research-questions.md). The current paper direction studies capability-separated privacy release for networked AI agents, rather than treating Long Gate as merely a local anonymization utility.

## Reproducibility pipeline

The artifact runner records:

- exact Long Gate source commit when available;
- Git checkout/event SHA separately when CI tests a merge ref;
- configuration SHA-256;
- Python and platform metadata;
- logical CPU count and system RAM when detectable;
- experiment ID and seed;
- per-run wall-clock duration;
- raw numeric metrics only — never raw private rows or source narratives.

Run the smoke suite:

```bash
make research-smoke
```

It currently runs three pieces:

```text
multi-seed structured audit smoke
        +
synthetic semantic red-team
        +
release-boundary attack harness
```

Run only the attack harnesses:

```bash
make research-redteam
```

The semantic smoke comparison includes:

- `identity` — negative control / no transformation;
- `deterministic-regex` — direct-pattern removal baseline.

Research adapters also exist for:

- local Presidio anonymization (`pip install -e '.[research-presidio]'`);
- one-pass verified local GGUF inference via Long Gate's llama.cpp transformer.

Those heavier baselines are **not** silently executed in GitHub CI. Their model/dependency versions must be frozen in the real paper configuration.

Equivalent core commands:

```bash
python -m research.run_experiments \
  --config research/configs/paper-smoke.json \
  --out research/results/paper-smoke

python -m research.aggregate_results \
  research/results/paper-smoke/runs.jsonl \
  --out research/results/paper-smoke

python -m research.semantic_redteam \
  --corpus research/redteam/semantic_synthetic_v1.jsonl \
  --baseline identity \
  --baseline deterministic-regex \
  --out research/results/paper-smoke

python -m research.release_boundary_redteam \
  --out research/results/paper-smoke
```

The generated directory contains only experiment provenance/metrics, for example:

```text
manifest.json
runs.jsonl
summary.json
summary.md
semantic-redteam-runs.jsonl
semantic-redteam-summary.json
release-boundary-runs.jsonl
release-boundary-summary.json
```

`research/results/` is ignored by Git by default. Raw run outputs should be archived deliberately for a paper artifact release rather than silently committed during development.

## Synthetic red-team scope

`redteam/semantic_synthetic_v1.jsonl` contains fictional/synthetic English cases for:

- direct contact/network identifiers;
- exact age/date reuse;
- rare-event leakage;
- relationship leakage;
- combination uniqueness;
- instruction-like text embedded in the source.

The runner never writes source/candidate narratives into result files; it writes case IDs, baseline IDs, failed-condition codes, and aggregate numeric metrics.

The synthetic corpus is useful for development, controlled counterexamples, and ablation plumbing. It is **not an independent external benchmark** and does not establish real-world anonymity.

## Release-boundary harness

`release_boundary_redteam.py` measures implemented behavior for:

- valid authorized read control;
- purpose mismatch;
- post-approval mutation;
- arbitrary-file approval;
- workspace path escape;
- egress-manifest hash mismatch;
- directory-only workspace vs Long Gate's approved workspace on an unapproved file.

This directly supports RQ1, but a paper should still compare against clearly defined external/system baselines rather than treating the internal directory-only control as representative of all competing systems.

## What is not complete yet

The repository does **not** currently claim that the full paper evaluation is complete. Before a full-paper submission, the matrix in [`experiment-matrix.md`](experiment-matrix.md) should still gain real runs covering:

- Presidio/NER and one-pass local-LLM baselines on independent data;
- full Long Gate semantic ablations;
- stronger inference-based rare-event, relationship, combination, and auxiliary-data attackers;
- one or more independent public text-anonymization datasets;
- privacy and downstream-utility metrics appropriate to those datasets;
- repeated seeds / repeated model runs where stochasticity applies;
- hardware/runtime evaluation across representative model tiers.

## Safety boundary

Research tooling must never weaken Long Gate release policy. In particular:

- semantic outputs remain local-only under the current product baseline;
- the runner must not upload datasets, prompts, transformed narratives, or model artifacts;
- experiment manifests should contain metadata and aggregate metrics, not source records;
- external datasets must retain their own licenses and provenance documentation.
