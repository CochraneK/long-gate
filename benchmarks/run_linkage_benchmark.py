from __future__ import annotations

import json
from pathlib import Path

from longgate.backends.demo import DemoBackend
from longgate.inspect import profile_dataframe
from longgate.io import load_table
from longgate.privacy_attacks import (
    unique_linkage_diagnostic,
)


def main() -> None:
    source = Path(
        "benchmarks/data/adversarial_source.csv"
    )
    if not source.exists():
        raise SystemExit(
            "Generate benchmark data first: "
            "python benchmarks/generate_adversarial.py"
        )

    raw = load_table(source)
    profiles = profile_dataframe(
        raw
    )
    synthetic = DemoBackend().generate(
        raw,
        profiles,
        seed=17,
    )
    auxiliary = raw[
        [
            "age",
            "city",
            "group",
        ]
    ].copy()
    result = unique_linkage_diagnostic(
        synthetic,
        auxiliary,
        [
            "age",
            "city",
            "group",
        ],
    )
    print(
        json.dumps(
            {
                "benchmark": (
                    "auxiliary-linkage-v0"
                ),
                "result": result.to_dict(),
                "note": (
                    "Exact quasi-identifier linkage diagnostic "
                    "against a synthetic benchmark fixture."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
