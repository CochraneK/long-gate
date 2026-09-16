# Release evidence gates

Long Gate deliberately separates **evidence** from **authorization**.

A metric passing a threshold never becomes an automatic permission to send private-derived data to a networked agent.

## Semantic text evidence

Every local semantic transformation now records a `semantic-release-evidence-v1` object.

Current mechanical criteria for becoming **eligible for manual review** are:

| Check | Threshold |
|---|---:|
| direct PII pattern hits | 0 |
| exact source numeric tokens reused | 0 |
| normalized 32-character n-gram reuse rate | ≤ 1% |
| reused distinctive long-token rate | ≤ 5% |
| transformed output length | ≥ 80 characters |

Even when all checks pass:

```json
{
  "eligible_for_manual_review": true,
  "manual_review_required": true,
  "automatic_release_allowed": false
}
```

These checks detect several concrete copying/identity-leak signals. They do **not** prove semantic anonymity.

## Row-level synthetic production evidence

Long Gate also has an executable `row-level-release-evidence-v1` checklist.

Create a JSON file with exactly these fields:

```json
{
  "backend_approved": true,
  "direct_pii_hits": 0,
  "exact_row_overlap": 0,
  "identifier_overlap": 0,
  "rare_quasi_overlap": 0,
  "near_copy_rate": 0.001,
  "membership_max_auc": 0.55,
  "attribute_inference_uplift": 0.02,
  "longitudinal_linkage_rate": 0.01,
  "benchmark_reproducible": true,
  "policy_reviewed": true,
  "human_review_recorded": true
}
```

Evaluate it:

```bash
longgate row-release-check evidence.json
```

Default evidence thresholds are:

- near-copy rate ≤ 1%;
- strongest bounded membership attack AUC ≤ 0.60;
- attribute-inference uplift ≤ 0.10;
- longitudinal linkage rate ≤ 0.05;
- no direct PII, exact rows, identifiers, or rare quasi-identifier overlap;
- benchmark reproducibility, policy review, and recorded human review are all required.

Missing attack evidence fails closed.

### Pre-1.0 hard lock

Even a fully satisfied evidence package returns:

```json
{
  "criteria_satisfied": true,
  "release_allowed": false,
  "next_action": "future_manual_policy_decision"
}
```

The pre-1.0 product therefore has **criteria without an unlock**. A future release would need an explicit policy/version decision to add a release mechanism.

## Why no composite privacy score?

Membership, linkage, attribute inference, copying, direct PII, and semantic disclosure are different failure modes. Long Gate keeps them separate rather than averaging them into a reassuring number.
