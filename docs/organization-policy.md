# Organization privacy profiles

Long Gate supports organization-defined JSON privacy profiles so thresholds can be reviewed, versioned, and reproduced instead of living in informal instructions.

Start from:

```text
policy/example-profile.json
```

Use it with structured processing:

```bash
longgate run study.csv --profile-file policy/my-organization.json
```

Or exact local statistics:

```bash
longgate exact study.csv describe --profile-file policy/my-organization.json
```

## Schema

```json
{
  "name": "my-organization",
  "min_dataset_size": 50,
  "min_group_size": 12,
  "rare_k": 12,
  "max_near_copy_rate": 0.005,
  "row_level_synthetic_egress": false,
  "description": "Reviewed engineering policy."
}
```

Unknown fields and malformed values fail closed.

## Pre-1.0 safety boundary

A custom policy file **cannot** set `row_level_synthetic_egress` to `true` in the current baseline.

That restriction is deliberate: an organization should not be able to turn an unreviewed backend into a row-level release mechanism by changing one JSON flag.

Custom files can make the policy stricter and reproducible. Row-level release remains a separate future evidence/review problem.

## Provenance

For file-based profiles the run manifest records:

- profile contents;
- policy filename;
- SHA-256 of the policy file.

This allows an audit to verify which reviewed policy produced a release decision without storing the user's full local filesystem path.
