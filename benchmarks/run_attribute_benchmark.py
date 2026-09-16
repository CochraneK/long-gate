from __future__ import annotations

import json
from pathlib import Path

from longgate.backends.demo import DemoBackend
from longgate.inspect import profile_dataframe
from longgate.io import load_table
from longgate.privacy_attacks import attribute_inference_diagnostic


def main() -> None:
    source = Path("benchmarks/data/adversarial_source.csv")
    if not source.exists():
        raise SystemExit(
            "Generate benchmark data first: "
            "python benchmarks/generate_adversarial.py"
        )

    raw = load_table(source)
    profiles = profile_dataframe(raw)
    synthetic = DemoBackend().generate(
        raw,
        profiles,
        seed=23,
    )
    result = attribute_inference_diagnostic(
        synthetic,
        raw,
        ["age", "city", "group"],
        "condition",
    )
    print(
        json.dumps(
            {
                "benchmark": "attribute-inference-v0",
                "result": result.to_dict(),
                "note": (
                    "Categorical modal-mapping attack using synthetic "
                    "quasi-identifier groups; not a general privacy proof."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
