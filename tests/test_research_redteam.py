from __future__ import annotations

import json
from pathlib import Path

from research.release_boundary_redteam import run_release_boundary_redteam, summarize as summarize_boundary
from research.semantic_baselines import deterministic_regex_baseline
from research.semantic_redteam import run_redteam, summarize as summarize_semantic, write_outputs

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "research" / "redteam" / "semantic_synthetic_v1.jsonl"


def test_deterministic_baseline_removes_direct_patterns_but_retains_utility() -> None:
    source = (
        "Workplace stress improved with support. Contact avery.example@example.com "
        "or +44 7700 900123 from postcode SW1A 1AA and IP 192.0.2.1."
    )
    transformed = deterministic_regex_baseline(source)
    assert "avery.example@example.com" not in transformed
    assert "+44 7700 900123" not in transformed
    assert "SW1A 1AA" not in transformed
    assert "192.0.2.1" not in transformed
    assert "Workplace stress" in transformed
    assert "support" in transformed


def test_semantic_redteam_outputs_metrics_only(tmp_path: Path) -> None:
    records = run_redteam(CORPUS, ["identity", "deterministic-regex"])
    summary = write_outputs(records, tmp_path)
    serialized = (tmp_path / "semantic-redteam-runs.jsonl").read_text(encoding="utf-8")

    assert summary["record_count"] == 16
    assert "identity" in summary["baselines"]
    assert "deterministic-regex" in summary["baselines"]
    assert "avery.example@example.com" not in serialized
    assert "Northbridge Xenon Rescue Collective" not in serialized
    assert all("source" not in record for record in records)
    assert all("candidate" not in record for record in records)


def test_deterministic_baseline_improves_direct_pii_cases() -> None:
    records = run_redteam(CORPUS, ["identity", "deterministic-regex"])
    summary = summarize_semantic(records)
    identity = summary["baselines"]["identity"]["by_attack_family"]["direct-pii"]
    deterministic = summary["baselines"]["deterministic-regex"]["by_attack_family"]["direct-pii"]
    assert identity["mean_metrics"]["attack_success"] == 1.0
    assert deterministic["mean_metrics"]["attack_success"] < identity["mean_metrics"]["attack_success"]
    assert deterministic["mean_metrics"]["utility_retention_rate"] > 0.0


def test_release_boundary_blocks_attacks_and_keeps_control_working() -> None:
    records = run_release_boundary_redteam()
    summary = summarize_boundary(records)
    long_gate = summary["baselines"]["long-gate-approved-workspace"]
    directory_only = summary["baselines"]["directory-only-workspace"]

    assert long_gate["attack_success_rate"] == 0.0
    assert long_gate["authorized_success_rate"] == 1.0
    assert long_gate["policy_accuracy"] == 1.0
    assert directory_only["attack_success_rate"] == 1.0


def test_release_boundary_records_do_not_embed_artifact_contents() -> None:
    records = run_release_boundary_redteam()
    serialized = json.dumps(records)
    assert "mean_score" not in serialized
    assert "synthetic private-looking material" not in serialized
    assert "outside workspace" not in serialized
