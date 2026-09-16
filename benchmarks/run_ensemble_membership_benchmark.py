from __future__ import annotations

import json
from pathlib import Path

from longgate.backends.demo import DemoBackend
from longgate.inspect import profile_dataframe
from longgate.io import load_table
from longgate.privacy_attacks import ensemble_membership_diagnostic


def main() -> None:
    source = Path("benchmarks/data/adversarial_source.csv")
    if not source.exists():
        raise SystemExit(
            "Generate benchmark data first: "
            "python benchmarks/generate_adversarial.py"
        )

    full = load_table(source)
    midpoint = len(full) // 2
    members = full.iloc[:midpoint].reset_index(drop=True)
    holdout = full.iloc[midpoint:].reset_index(drop=True)
    profiles = profile_dataframe(members)
    synthetic = DemoBackend().generate(members, profiles, seed=11)
    columns = ["age", "PHQ", "GAD", "reaction_time"]

    result = ensemble_membership_diagnostic(
        members,
        holdout,
        synthetic,
        columns,
        max_subset_size=2,
    )
    print(
        json.dumps(
            {
                "benchmark": "ensemble-membership-v1",
                "result": result.to_dict(),
                "note": (
                    "Bounded ensemble of distance attacks; strongest observed "
                    "AUC is reported conservatively and is not a privacy proof."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
