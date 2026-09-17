from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def _numeric_metrics(record: dict[str, Any]) -> dict[str, float]:
    metrics = record.get("metrics", {})
    if not isinstance(metrics, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in metrics.items():
        if isinstance(value, bool):
            out[key] = float(int(value))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            out[key] = float(value)
    duration = record.get("duration_seconds")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        out["duration_seconds"] = float(duration)
    return out


def _summary(values: list[float]) -> dict[str, float | int | None]:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "sample_sd": None, "ci95_low": None, "ci95_high": None}
    mean = statistics.fmean(values)
    sample_sd = statistics.stdev(values) if n > 1 else 0.0
    margin = 1.96 * sample_sd / math.sqrt(n) if n > 1 else 0.0
    return {
        "n": n,
        "mean": round(mean, 8),
        "sample_sd": round(sample_sd, 8),
        "ci95_low": round(mean - margin, 8),
        "ci95_high": round(mean + margin, 8),
    }


def aggregate(records: list[dict[str, Any]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        experiment_id = record.get("experiment_id")
        if isinstance(experiment_id, str) and experiment_id:
            grouped[experiment_id].append(record)

    experiments: dict[str, object] = {}
    for experiment_id, group in sorted(grouped.items()):
        metric_values: dict[str, list[float]] = defaultdict(list)
        for record in group:
            for key, value in _numeric_metrics(record).items():
                metric_values[key].append(value)
        experiments[experiment_id] = {
            "runs": len(group),
            "seeds": sorted(record["seed"] for record in group if isinstance(record.get("seed"), int)),
            "metrics": {key: _summary(values) for key, values in sorted(metric_values.items())},
        }

    return {
        "schema_version": 1,
        "experiment_count": len(experiments),
        "run_count": len(records),
        "experiments": experiments,
        "statistics_note": (
            "95% intervals are descriptive normal-approximation intervals across repeated runs. "
            "Do not interpret repeated seeds as independent population samples."
        ),
    }


def _markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Research summary",
        "",
        "> Generated from normalized `runs.jsonl`; this table is descriptive, not a privacy certification.",
        "",
        "| Experiment | Metric | n | Mean | Sample SD | Approx. 95% CI |",
        "|---|---|---:|---:|---:|---:|",
    ]
    experiments = summary.get("experiments", {})
    if isinstance(experiments, dict):
        for experiment_id, payload in experiments.items():
            if not isinstance(payload, dict):
                continue
            metrics = payload.get("metrics", {})
            if not isinstance(metrics, dict):
                continue
            for metric, stats in metrics.items():
                if not isinstance(stats, dict):
                    continue
                lines.append(
                    "| {experiment} | {metric} | {n} | {mean} | {sd} | [{low}, {high}] |".format(
                        experiment=experiment_id,
                        metric=metric,
                        n=stats.get("n"),
                        mean=stats.get("mean"),
                        sd=stats.get("sample_sd"),
                        low=stats.get("ci95_low"),
                        high=stats.get("ci95_high"),
                    )
                )
    lines.append("")
    lines.append(str(summary.get("statistics_note", "")))
    lines.append("")
    return "\n".join(lines)


def load_records(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not an object")
            records.append(value)
    if not records:
        raise ValueError("no experiment records found")
    return records


def write_summary(records_path: str | Path, out_dir: str | Path) -> dict[str, object]:
    records = load_records(records_path)
    summary = aggregate(records)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "summary.md").write_text(_markdown(summary), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate normalized Long Gate research results.")
    parser.add_argument("records", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    summary = write_summary(args.records, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
