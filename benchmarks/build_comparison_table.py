from __future__ import annotations

import json
from pathlib import Path


PRIMARY_METRICS = {
    "distance-membership-v0": ["auc"],
    "ensemble-membership-v1": ["max_auc", "median_auc", "attacks_run"],
    "auxiliary-linkage-v0": ["unique_linkage_rate", "unique_matches"],
    "attribute-inference-v0": ["coverage", "attack_accuracy", "accuracy_uplift"],
    "longitudinal-linkage-v0": ["unique_linkage_rate", "unique_link_precision"],
    "fuzzy-longitudinal-linkage-v1": [
        "unique_linkage_rate",
        "unique_link_precision",
    ],
    "k-anonymity-v0": [
        "min_equivalence_class",
        "unique_row_rate",
        "rows_below_k_rate",
    ],
}


def _display(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def main() -> None:
    rows: list[tuple[str, str, str]] = []
    machine: list[dict[str, object]] = []
    for path in sorted(Path(".").glob("benchmark-*.json")):
        if path.name in {"benchmark-summary.json"}:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        name = str(data.get("benchmark", path.stem))
        result = data.get("result", {})
        if not isinstance(result, dict):
            continue
        metrics = PRIMARY_METRICS.get(name)
        if metrics is None:
            metrics = [
                key
                for key, value in result.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ][:4]
        selected = {key: result.get(key) for key in metrics}
        machine.append(
            {
                "benchmark": name,
                "source_file": path.name,
                "metrics": selected,
            }
        )
        for key, value in selected.items():
            rows.append((name, key, _display(value)))

    payload = {
        "schema_version": 1,
        "summary": "cross-attack benchmark observations; not a composite privacy score",
        "benchmarks": machine,
        "row_level_release_allowed": False,
    }
    Path("benchmark-summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Long Gate privacy benchmark comparison",
        "",
        "> These are attack-specific observations, not a composite privacy score "
        "or anonymity certificate.",
        "",
        "| Benchmark | Metric | Observed |",
        "|---|---|---:|",
    ]
    lines.extend(
        f"| {benchmark} | {metric} | {value} |"
        for benchmark, metric, value in rows
    )
    lines.extend(
        [
            "",
            "**Row-level release remains disabled.** Benchmark evidence is used to "
            "find failures, not to auto-authorize egress.",
            "",
        ]
    )
    Path("benchmark-summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
