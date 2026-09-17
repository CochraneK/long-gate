from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.aggregate_results import aggregate, load_records, write_summary
from research.run_experiments import run_suite, validate_config


def _config() -> dict[str, object]:
    return {
        "schema_version": 1,
        "suite": "test-suite",
        "purpose": "test only",
        "seeds": [3, 5],
        "experiments": [
            {"id": "structured", "kind": "structured_demo_audit", "rows": 40}
        ],
    }


def test_validate_config_rejects_unknown_experiment_kind() -> None:
    config = _config()
    config["experiments"] = [{"id": "bad", "kind": "remote_magic", "rows": 40}]
    with pytest.raises(ValueError, match="unsupported experiment kind"):
        validate_config(config)


def test_run_suite_records_provenance_without_source_rows(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config()), encoding="utf-8")
    out = tmp_path / "out"

    manifest = run_suite(config_path, out)
    records = load_records(out / "runs.jsonl")

    assert manifest["run_count"] == 2
    assert manifest["configuration"]["sha256"]
    assert manifest["environment"]["python"]
    assert len(records) == 2
    assert {record["seed"] for record in records} == {3, 5}
    assert all("metrics" in record for record in records)
    assert all("participant_id" not in json.dumps(record) for record in records)
    assert all("Synthetic Person" not in json.dumps(record) for record in records)


def test_aggregate_produces_descriptive_statistics() -> None:
    records = [
        {
            "experiment_id": "x",
            "seed": 1,
            "duration_seconds": 1.0,
            "metrics": {"attack_success": 0, "utility": 0.8},
        },
        {
            "experiment_id": "x",
            "seed": 2,
            "duration_seconds": 3.0,
            "metrics": {"attack_success": 1, "utility": 0.6},
        },
    ]
    summary = aggregate(records)
    payload = summary["experiments"]["x"]
    assert payload["runs"] == 2
    assert payload["metrics"]["attack_success"]["mean"] == 0.5
    assert payload["metrics"]["duration_seconds"]["mean"] == 2.0
    assert payload["metrics"]["utility"]["sample_sd"] > 0


def test_write_summary_creates_json_and_markdown(tmp_path: Path) -> None:
    records = tmp_path / "runs.jsonl"
    records.write_text(
        json.dumps(
            {
                "experiment_id": "x",
                "seed": 7,
                "duration_seconds": 1.25,
                "metrics": {"score": 0.75},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    summary = write_summary(records, tmp_path / "summary")
    assert summary["run_count"] == 1
    assert (tmp_path / "summary" / "summary.json").is_file()
    markdown = (tmp_path / "summary" / "summary.md").read_text(encoding="utf-8")
    assert "Approx. 95% CI" in markdown
    assert "x" in markdown
