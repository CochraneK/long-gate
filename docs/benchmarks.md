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

## Attribute inference diagnostic

```bash
python benchmarks/run_attribute_benchmark.py
```

This attack learns the modal categorical sensitive value for each observed quasi-identifier combination in the synthetic dataset, then measures:

- coverage on target rows;
- attack accuracy among covered rows;
- modal-baseline accuracy;
- accuracy uplift over that baseline.

Coverage and accuracy remain separate. A narrow attack with high accuracy is not averaged into a misleading single privacy score.

## Longitudinal linkage diagnostic

```bash
python benchmarks/run_longitudinal_benchmark.py
```

This attack asks whether records can be uniquely linked across two time points using stable quasi-identifiers. A local ground-truth entity column is used only to calculate precision; entity values are never emitted in results.

It reports unique-linkage rate and precision for this defined exact-matching attack.

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
- richer attribute-inference variants;
- auxiliary-dataset linkage variants;
- probabilistic / fuzzy longitudinal linkage;
- DP-backend evaluation;
- machine-readable release comparison tables.
