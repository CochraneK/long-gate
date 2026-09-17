from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.datasets.prepare_tab import verify_prepared_tab
from research.datasets.tab_adapter import TabDocument, load_tab_documents, score_candidate
from research.semantic_baselines import transform_baseline


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_path(dataset_dir: Path, split: str) -> Path:
    names = {
        "train": "echr_train.json",
        "dev": "echr_dev.json",
        "test": "echr_test.json",
    }
    if split not in names:
        raise ValueError(f"unsupported TAB split: {split}")
    return dataset_dir / names[split]


def _model_provenance(model_path: Path | None) -> dict[str, object] | None:
    if model_path is None:
        return None
    resolved = model_path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(model_path)
    return {
        "filename": resolved.name,
        "sha256": _sha256_file(resolved),
        "bytes": resolved.stat().st_size,
    }


def _evaluate_document(
    document: TabDocument,
    baseline: str,
    *,
    model_path: Path | None,
) -> dict[str, object]:
    started = time.perf_counter()
    try:
        candidate = transform_baseline(
            baseline,
            document.text,
            model_path=model_path,
            language="en",
        )
        metrics = score_candidate(document, candidate)
        return {
            "schema_version": 1,
            "experiment_id": f"tab-v1:{baseline}",
            "dataset": "tab-v1",
            "split": document.dataset_type,
            "doc_id": document.doc_id,
            "baseline": baseline,
            "status": "success",
            "duration_seconds": round(time.perf_counter() - started, 6),
            "metrics": metrics,
        }
    except Exception as exc:  # keep failed runs in denominators without leaking local paths/messages
        return {
            "schema_version": 1,
            "experiment_id": f"tab-v1:{baseline}",
            "dataset": "tab-v1",
            "split": document.dataset_type,
            "doc_id": document.doc_id,
            "baseline": baseline,
            "status": "failure",
            "duration_seconds": round(time.perf_counter() - started, 6),
            "error_type": type(exc).__name__,
            "metrics": {},
        }


def run_tab_baselines(
    dataset_dir: str | Path,
    *,
    split: str,
    baselines: list[str],
    model_path: str | Path | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    dataset = Path(dataset_dir).expanduser().resolve()
    errors = verify_prepared_tab(dataset)
    if errors:
        raise RuntimeError("Prepared TAB dataset failed verification: " + "; ".join(errors))
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")

    documents = load_tab_documents(_split_path(dataset, split))
    selected = documents[offset : offset + limit if limit is not None else None]
    resolved_model = Path(model_path) if model_path is not None else None
    records: list[dict[str, object]] = []
    for baseline in baselines:
        for document in selected:
            records.append(
                _evaluate_document(
                    document,
                    baseline,
                    model_path=resolved_model,
                )
            )

    provenance = json.loads((dataset / "tab-provenance.json").read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 1,
        "suite": "tab-v1-baselines",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "id": "tab-v1",
            "repository_commit": provenance.get("repository_commit"),
            "split": split,
            "split_sha256": provenance.get("files", {}).get(split, {}).get("sha256"),
            "selected_documents": len(selected),
            "offset": offset,
            "limit": limit,
        },
        "baselines": baselines,
        "model": _model_provenance(resolved_model),
        "record_count": len(records),
        "privacy_note": (
            "Result records contain public TAB document IDs and aggregate literal metrics only. "
            "Source/candidate court-case text is not copied into result files."
        ),
        "metric_note": (
            "Literal retention/removal is a Long Gate bridge metric for generative outputs, "
            "not the official TAB evaluation score."
        ),
    }
    return records, manifest


def _macro_mean(records: list[dict[str, object]], metric: str) -> float | None:
    values = [
        float(record["metrics"][metric])
        for record in records
        if record.get("status") == "success"
        and isinstance(record.get("metrics"), dict)
        and metric in record["metrics"]
    ]
    return round(sum(values) / len(values), 6) if values else None


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[str(record["baseline"])].append(record)

    baselines: dict[str, object] = {}
    for baseline, group in sorted(grouped.items()):
        successful = [record for record in group if record.get("status") == "success"]
        failed = [record for record in group if record.get("status") != "success"]

        def total(metric: str) -> int:
            return sum(
                int(record["metrics"].get(metric, 0))
                for record in successful
                if isinstance(record.get("metrics"), dict)
            )

        sensitive_total = total("sensitive_mentions")
        sensitive_retained = total("sensitive_literals_retained")
        no_mask_total = total("no_mask_mentions")
        no_mask_retained = total("no_mask_literals_retained")
        direct_total = total("direct_mentions")
        direct_retained = total("direct_literals_retained")
        quasi_total = total("quasi_mentions")
        quasi_retained = total("quasi_literals_retained")

        baselines[baseline] = {
            "documents": len(group),
            "successful_documents": len(successful),
            "failed_documents": len(failed),
            "failure_rate": round(len(failed) / len(group), 6) if group else 0.0,
            "micro": {
                "sensitive_literal_retention_rate": round(
                    sensitive_retained / sensitive_total, 6
                )
                if sensitive_total
                else None,
                "sensitive_literal_removal_rate": round(
                    1.0 - (sensitive_retained / sensitive_total), 6
                )
                if sensitive_total
                else None,
                "direct_literal_retention_rate": round(direct_retained / direct_total, 6)
                if direct_total
                else None,
                "quasi_literal_retention_rate": round(quasi_retained / quasi_total, 6)
                if quasi_total
                else None,
                "no_mask_literal_retention_rate": round(no_mask_retained / no_mask_total, 6)
                if no_mask_total
                else None,
            },
            "macro": {
                "sensitive_literal_removal_rate": _macro_mean(
                    successful, "sensitive_literal_removal_rate"
                ),
                "no_mask_literal_retention_rate": _macro_mean(
                    successful, "no_mask_literal_retention_rate"
                ),
                "duration_seconds": _macro_mean(successful, "duration_seconds"),
            },
            "failure_types": sorted(
                {
                    str(record.get("error_type"))
                    for record in failed
                    if record.get("error_type")
                }
            ),
        }

    return {
        "schema_version": 1,
        "baselines": baselines,
        "metric_note": (
            "These literal metrics are transparent bridge metrics for generative text and "
            "must not be labeled as official TAB scores."
        ),
    }


def write_outputs(
    records: list[dict[str, object]],
    manifest: dict[str, object],
    out_dir: str | Path,
) -> dict[str, object]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "tab-runs.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (out / "tab-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = summarize(records)
    (out / "tab-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Long Gate semantic baselines on TAB v1.")
    parser.add_argument("--dataset-dir", required=True, type=Path)
    parser.add_argument("--split", choices=["train", "dev", "test"], default="dev")
    parser.add_argument("--baseline", action="append", dest="baselines", required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    records, manifest = run_tab_baselines(
        args.dataset_dir,
        split=args.split,
        baselines=args.baselines,
        model_path=args.model,
        limit=args.limit,
        offset=args.offset,
    )
    summary = write_outputs(records, manifest, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
