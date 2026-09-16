# Examples

All committed examples must be synthetic or otherwise non-sensitive.

## Structured demo

```bash
longgate inspect examples/demo.csv
longgate run examples/demo.csv --backend demo
```

The demo backend is intentionally blocked from row-level egress. A BLOCKED result is expected and demonstrates fail-closed behavior.

## Exact local analysis

Use a dataset with at least the minimum safe sample threshold:

```bash
longgate exact study.csv describe
longgate exact study.csv correlation
longgate exact study.csv group-summary --group-by group --value score
longgate exact study.csv ols --outcome score --predictor age --predictor group
```

Exact analyses run on the source data locally; only guarded aggregate results are returned.

## Trust Report

Each pipeline run writes a self-contained offline report under:

```text
longgate-runs/<run-id>/report/trust-report.html
```

The report contains counts, hashes, decisions, and audit facts rather than source rows.
