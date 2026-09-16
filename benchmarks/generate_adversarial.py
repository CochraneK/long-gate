from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def build_dataset(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    cities = ["Northbridge", "Eastmere", "Westhaven", "Southfield"]
    condition_by_city = {
        "Northbridge": "C1",
        "Eastmere": "C2",
        "Westhaven": "C3",
        "Southfield": "C4",
    }
    for i in range(n):
        city = rng.choice(cities)
        group = rng.choice(["A", "B"])
        condition = (
            condition_by_city[city]
            if rng.random() < 0.82
            else rng.choice(["C1", "C2", "C3", "C4"])
        )
        rows.append(
            {
                "participant_id": 100000 + i,
                "name": f"Synthetic Person {i:04d}",
                "email": f"synthetic-{i}@example.invalid",
                "age": rng.randint(18, 70),
                "city": city,
                "PHQ": rng.randint(0, 27),
                "GAD": rng.randint(0, 21),
                "reaction_time": int(rng.gauss(650, 80)),
                "group": group,
                "condition": condition,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = Path("benchmarks/data/adversarial_source.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    build_dataset().to_csv(out, index=False)
    print(out)
