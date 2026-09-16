from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def build_dataset(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        rows.append(
            {
                "participant_id": 100000 + i,
                "name": f"Synthetic Person {i:04d}",
                "email": f"synthetic-{i}@example.invalid",
                "age": rng.randint(18, 70),
                "city": rng.choice(["Northbridge", "Eastmere", "Westhaven", "Southfield"]),
                "PHQ": rng.randint(0, 27),
                "GAD": rng.randint(0, 21),
                "reaction_time": int(rng.gauss(650, 80)),
                "group": rng.choice(["A", "B"]),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = Path("benchmarks/data/adversarial_source.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    build_dataset().to_csv(out, index=False)
    print(out)
