# Benchmarks and adversarial evaluation

A privacy gateway should be tested against deliberate failures, not only happy-path demo data.

Long Gate keeps benchmark claims conservative: a passing benchmark is evidence that a specific attack/check did not fail under that fixture. It is **not** proof that a dataset is anonymous.

## Structured adversarial fixture

Generate a fully synthetic benchmark source:

```bash
python benchmarks/generate_adversarial.py
```

Then run the current audit suite:

```bash
python benchmarks/run_privacy_benchmark.py
```

The fixture is designed to evolve into a corpus of explicit attacks:

- exact row copies;
- direct identifier reuse;
- rare quasi-identifier reproduction;
- numeric near copies;
- deterministic pseudonymization;
- small groups;
- membership-inference probes;
- linkage against auxiliary datasets.

## Benchmark rules

1. Benchmark source data committed to this repository must be synthetic.
2. Every metric must be reproducible.
3. No “privacy score” should be invented without a clear definition.
4. A benchmark pass must not be described as a formal anonymity guarantee.
5. Threshold changes require tests and threat-model justification.

## Planned outputs

Future benchmark runs should emit machine-readable JSON plus a human-readable comparison table suitable for release notes.
