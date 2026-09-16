from __future__ import annotations

import json
from pathlib import Path

from longgate.audit import audit_dataset
from longgate.backends.demo import DemoBackend
from longgate.inspect import profile_dataframe
from longgate.io import load_table


def main() -> None:
    source = Path("benchmarks/data/adversarial_source.csv")
    if not source.exists():
        raise SystemExit("Generate benchmark data first: python benchmarks/generate_adversarial.py")

    raw = load_table(source)
    profiles = profile_dataframe(raw)
    backend = DemoBackend()
    syn = backend.generate(raw, profiles, seed=7)
    audit = audit_dataset(
        raw,
        syn,
        profiles,
        backend.certified_for_egress,
    )

    print(
        json.dumps(
            {
                "benchmark": "adversarial-structured-v0",
                "rows": len(raw),
                "backend": backend.name,
                "audit": audit.to_dict(),
                "note": (
                    "This benchmark demonstrates measurable checks. "
                    "It is not a privacy certification."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
