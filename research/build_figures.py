from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_metric_figure(summary_path: str | Path, metric: str, output_path: str | Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - optional research dependency
        raise RuntimeError("Install the research extra: pip install -e '.[research]'") from exc

    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    experiments = summary.get("experiments", {})
    if not isinstance(experiments, dict):
        raise ValueError("summary experiments must be an object")

    labels: list[str] = []
    means: list[float] = []
    errors: list[float] = []
    for experiment_id, payload in sorted(experiments.items()):
        if not isinstance(payload, dict):
            continue
        metrics = payload.get("metrics", {})
        if not isinstance(metrics, dict) or metric not in metrics:
            continue
        stats = metrics[metric]
        if not isinstance(stats, dict) or stats.get("mean") is None:
            continue
        mean = float(stats["mean"])
        low = float(stats.get("ci95_low", mean))
        high = float(stats.get("ci95_high", mean))
        labels.append(experiment_id)
        means.append(mean)
        errors.append(max(high - mean, mean - low, 0.0))

    if not labels:
        raise ValueError(f"metric not found in summary: {metric}")

    width = max(6.0, len(labels) * 1.4)
    figure, axis = plt.subplots(figsize=(width, 4.5))
    positions = list(range(len(labels)))
    axis.bar(positions, means, yerr=errors, capsize=4)
    axis.set_xticks(positions, labels, rotation=20, ha="right")
    axis.set_ylabel(metric)
    axis.set_title(f"Long Gate research summary: {metric}")
    figure.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a figure from Long Gate research summary JSON.")
    parser.add_argument("summary", type=Path)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    build_metric_figure(args.summary, args.metric, args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
