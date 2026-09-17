# Dataset provenance

Do not copy evaluation datasets into this directory merely for convenience.

Each paper dataset should have a small manifest recording:

- canonical name and version/date;
- source URL or DOI;
- license / terms and whether redistribution is allowed;
- expected file checksum(s) when stable;
- preprocessing script and parameters;
- split definition;
- role: development, main evaluation, or red-team;
- any sensitive-data handling constraints.

A suggested sidecar shape is:

```json
{
  "schema_version": 1,
  "id": "example-dataset-v1",
  "role": "main-evaluation",
  "source": "https://example.org/dataset",
  "license": "verify-from-source",
  "redistributable": false,
  "expected_sha256": null,
  "preprocessing": "research/datasets/prepare_example.py",
  "notes": "Do not publish dataset bytes unless redistribution is explicitly permitted."
}
```

The paper artifact should prefer download/prepare instructions over republishing third-party data. If a dataset contains real sensitive information, it must not be added to the public artifact simply because the research runner can process it.
