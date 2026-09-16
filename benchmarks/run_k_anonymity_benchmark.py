from __future__ import annotations

import json
from pathlib import Path

from longgate.io import load_table
from longgate.privacy_attacks import (
    k_anonymity_diagnostic,
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
    result = k_anonymity_diagnostic(
        raw,
        [
            "age",
            "city",
            "group",
        ],
        k=5,
    )
    print(
        json.dumps(
            {
                "benchmark": (
                    "quasi-k-anonymity-v0"
                ),
                "result": result.to_dict(),
                "note": (
                    "Equivalence-class diagnostic only; "
                    "meeting k does not prove anonymity."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
