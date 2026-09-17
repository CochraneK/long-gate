# Long Gate research artifact

This directory is the **paper-evidence layer** for Long Gate. The product runtime lives in `src/longgate/`; engineering regression tests live in `tests/` and `benchmarks/`. Research code here exists to make scientific claims reproducible.

The separation is deliberate:

```text
src/ + tests/ + benchmarks/   -> is the software behaving as intended?
research/                     -> do the paper's empirical claims hold?
```

## Integrity rule

`make research-smoke` is a CI-safe artifact-pipeline smoke test. It is **not paper evidence** and must never be cited as a completed experiment.

A future `research-paper` target should only be added after the paper protocol, datasets, baselines, metrics, and main experiment configuration are frozen.

## Current research questions

See [`research-questions.md`](research-questions.md). The current paper direction studies capability-separated privacy release for networked AI agents, rather than treating Long Gate as merely a local anonymization utility.

## Reproducibility pipeline

The artifact runner records:

- exact Long Gate Git commit when available;
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

Equivalent commands:

```bash
python -m research.run_experiments \
  --config research/configs/paper-smoke.json \
  --out research/results/paper-smoke

python -m research.aggregate_results \
  research/results/paper-smoke/runs.jsonl \
  --out research/results/paper-smoke
```

The generated directory contains:

```text
manifest.json       experiment provenance
runs.jsonl          one normalized record per seed/run
summary.json        grouped descriptive statistics
summary.md          paper-friendly Markdown table
```

`research/results/` is ignored by Git by default. Raw run outputs should be archived deliberately for a paper artifact release rather than silently committed during development.

## What is not complete yet

The repository does **not** currently claim that the full paper evaluation is complete. Before a full-paper submission, the matrix in [`experiment-matrix.md`](experiment-matrix.md) should be populated with real runs covering:

- deterministic/NER baselines;
- one-pass local-LLM baseline;
- Long Gate ablations;
- semantic privacy attacks including rare-event and relationship leakage;
- multiple public datasets and a documented synthetic red-team corpus;
- privacy and downstream-utility metrics;
- repeated seeds / repeated model runs where stochasticity applies;
- hardware/runtime evaluation across representative model tiers.

## Safety boundary

Research tooling must never weaken Long Gate release policy. In particular:

- semantic outputs remain local-only under the current product baseline;
- the runner must not upload datasets, prompts, transformed narratives, or model artifacts;
- experiment manifests should contain metadata and aggregate metrics, not source records;
- external datasets must retain their own licenses and provenance documentation.
