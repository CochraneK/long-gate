from __future__ import annotations

import json
from pathlib import Path

from longgate.io import load_table
from longgate.privacy_attacks import longitudinal_linkage_diagnostic


def main() -> None:
    source = Path("benchmarks/data/adversarial_source.csv")
    if not source.exists():
        raise SystemExit(
            "Generate benchmark data first: "
            "python benchmarks/generate_adversarial.py"
        )

    earlier = load_table(source)
    later = earlier.copy()
    later["PHQ"] = (later["PHQ"] + 1).clip(upper=27)
    later["GAD"] = (later["GAD"] + 1).clip(upper=21)
    later["reaction_time"] = later["reaction_time"] + 7

    result = longitudinal_linkage_diagnostic(
        earlier,
        later,
        ["age", "city", "group"],
        "participant_id",
    )
    print(
        json.dumps(
            {
                "benchmark": "longitudinal-linkage-v0",
                "result": result.to_dict(),
                "note": (
                    "Exact cross-time quasi-identifier linkage with local "
                    "ground truth; identifiers are not emitted in results."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
