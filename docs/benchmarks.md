# Benchmarks and adversarial evaluation

A privacy gateway should be tested against deliberate failures, not only happy-path demo data.

Long Gate keeps benchmark claims conservative: a passing benchmark is evidence about a specific attack and fixture. It is **not** proof that a dataset is anonymous.

## Generate the synthetic benchmark source

```bash
python benchmarks/generate_adversarial.py
```

All committed/generated benchmark source records are synthetic.

## Core structured audit

```bash
python benchmarks/run_privacy_benchmark.py
```

## Quasi-identifier equivalence classes

```bash
python benchmarks/run_k_anonymity_benchmark.py
```

This reports:

- minimum equivalence-class size;
- number/rate of unique records for selected quasi-identifiers;
- number/rate of records in classes smaller than a chosen `k`.

This is a **k-anonymity-style diagnostic**, not a declaration that the data is anonymous. It does not by itself address sensitive-attribute disclosure, auxiliary data, semantic linkage, or membership inference.

## Distance-based membership diagnostic

```bash
python benchmarks/run_membership_benchmark.py
```

This test asks whether rows used to generate a synthetic table are systematically closer to synthetic records than a holdout set.

It reports ROC-style AUC for this defined distance attack:

- ~0.5: attack is near chance;
- higher values: this attack distinguishes members more successfully.

This is not a general membership-inference guarantee.

## Auxiliary-data linkage diagnostic

```bash
python benchmarks/run_linkage_benchmark.py
```

This test performs exact matching on selected quasi-identifiers against an auxiliary table and reports the unique-linkage rate.

Again, it is one explicit attack, not a universal privacy score.

## Benchmark rules

1. Benchmark data committed to this repository must be synthetic.
2. Every metric must have a documented definition.
3. Do not invent composite “privacy scores” without a defensible model.
4. A benchmark pass is not an anonymity certificate.
5. Threshold changes require tests and threat-model rationale.
6. Attack implementations should be simple enough to inspect or delegated to mature upstream libraries when available.

## Planned expansion

- shadow-model membership inference where justified;
- nearest-neighbor / DCR variants;
- attribute inference;
- auxiliary-dataset linkage variants;
- longitudinal linkage;
- DP-backend evaluation;
- machine-readable release comparison tables.
