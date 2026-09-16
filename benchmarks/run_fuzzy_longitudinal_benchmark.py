from __future__ import annotations

import json
from pathlib import Path

from longgate.io import load_table
from longgate.privacy_attacks import fuzzy_longitudinal_linkage_diagnostic


def main() -> None:
    source = Path("benchmarks/data/adversarial_source.csv")
    if not source.exists():
        raise SystemExit(
            "Generate benchmark data first: "
            "python benchmarks/generate_adversarial.py"
        )

    earlier = load_table(source)
    later = earlier.copy()
    later["age"] = later["age"] + 1
    later["PHQ"] = (later["PHQ"] + 1).clip(upper=27)
    later["GAD"] = (later["GAD"] + 1).clip(upper=21)
    later["reaction_time"] = later["reaction_time"] + 7

    result = fuzzy_longitudinal_linkage_diagnostic(
        earlier,
        later,
        categorical_columns=["city", "group"],
        numeric_tolerances={
            "age": 1,
            "PHQ": 2,
            "GAD": 2,
            "reaction_time": 10,
        },
        entity_column="participant_id",
    )
    print(
        json.dumps(
            {
                "benchmark": "fuzzy-longitudinal-linkage-v1",
                "result": result.to_dict(),
                "note": (
                    "Bounded fuzzy cross-time linkage with local ground truth; "
                    "entity values are never emitted."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
