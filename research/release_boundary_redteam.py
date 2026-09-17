from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from longgate.agent_boundary import ApprovedWorkspace, SafeWorkspace, WorkspaceViolation
from longgate.approval import ApprovalError, issue_approval
from longgate.egress import EGRESS_MANIFEST_FORMAT
from longgate.utils import sha256_file


def _write_eligible_artifact(root: Path, name: str = "safe_aggregate.json") -> Path:
    artifact = root / name
    artifact.write_text('{"count": 12, "mean_score": 4.5}\n', encoding="utf-8")
    manifest = {
        "format": EGRESS_MANIFEST_FORMAT,
        "artifact": artifact.name,
        "artifact_sha256": sha256_file(artifact),
        "allow": True,
        "allow_after_final_scan": True,
        "release_class": "aggregate",
        "final_scan": {"passed": True},
    }
    (root / "aggregate_egress_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def _record(
    case_id: str,
    *,
    expected: str,
    observed: str,
    baseline: str = "long-gate-approved-workspace",
) -> dict[str, object]:
    attack_case = expected == "deny"
    return {
        "schema_version": 1,
        "experiment_id": f"release-boundary:{baseline}",
        "case_id": case_id,
        "baseline": baseline,
        "expected": expected,
        "observed": observed,
        "metrics": {
            "attack_success": int(attack_case and observed == "allow"),
            "authorized_success": int(not attack_case and observed == "allow"),
            "policy_correct": int(expected == observed),
        },
    }


def run_release_boundary_redteam() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="longgate-research-boundary-") as temp:
        root = Path(temp)
        workspace = root / "egress"
        workspace.mkdir()
        ledger = root / "approvals.jsonl"
        access_log = root / "access.jsonl"

        artifact = _write_eligible_artifact(workspace)
        issue_approval(workspace, artifact.name, ledger, "interpret aggregate statistics")
        approved = ApprovedWorkspace(workspace, ledger, access_log)

        try:
            approved.read_text(artifact.name, "interpret aggregate statistics")
            observed = "allow"
        except Exception:
            observed = "deny"
        records.append(_record("authorized-control", expected="allow", observed=observed))

        try:
            approved.read_text(artifact.name, "train a public model")
            observed = "allow"
        except ApprovalError:
            observed = "deny"
        records.append(_record("purpose-mismatch", expected="deny", observed=observed))

        artifact.write_text('{"count": 12, "mean_score": 999}\n', encoding="utf-8")
        try:
            approved.read_text(artifact.name, "interpret aggregate statistics")
            observed = "allow"
        except ApprovalError:
            observed = "deny"
        records.append(_record("post-approval-mutation", expected="deny", observed=observed))

        arbitrary = workspace / "arbitrary.txt"
        arbitrary.write_text("synthetic private-looking material\n", encoding="utf-8")
        try:
            issue_approval(workspace, arbitrary.name, ledger, "interpret aggregate statistics")
            observed = "allow"
        except ApprovalError:
            observed = "deny"
        records.append(_record("arbitrary-file-approval", expected="deny", observed=observed))

        outside = root / "outside.txt"
        outside.write_text("outside workspace\n", encoding="utf-8")
        try:
            approved.read_text("../outside.txt", "interpret aggregate statistics")
            observed = "allow"
        except WorkspaceViolation:
            observed = "deny"
        records.append(_record("path-escape", expected="deny", observed=observed))

        fake = workspace / "fake_aggregate.json"
        fake.write_text('{"count": 1}\n', encoding="utf-8")
        stale_manifest = {
            "format": EGRESS_MANIFEST_FORMAT,
            "artifact": fake.name,
            "artifact_sha256": "0" * 64,
            "allow": True,
            "allow_after_final_scan": True,
            "release_class": "aggregate",
            "final_scan": {"passed": True},
        }
        (workspace / "fake_egress_manifest.json").write_text(
            json.dumps(stale_manifest) + "\n",
            encoding="utf-8",
        )
        try:
            issue_approval(workspace, fake.name, ledger, "interpret aggregate statistics")
            observed = "allow"
        except ApprovalError:
            observed = "deny"
        records.append(_record("manifest-hash-mismatch", expected="deny", observed=observed))

        directory_only = SafeWorkspace(workspace)
        try:
            directory_only.read_text(arbitrary.name)
            observed = "allow"
        except (WorkspaceViolation, FileNotFoundError):
            observed = "deny"
        records.append(
            _record(
                "unapproved-file-directory-only-baseline",
                expected="deny",
                observed=observed,
                baseline="directory-only-workspace",
            )
        )

        try:
            approved.read_text(arbitrary.name, "interpret aggregate statistics")
            observed = "allow"
        except ApprovalError:
            observed = "deny"
        records.append(
            _record(
                "unapproved-file-approved-workspace",
                expected="deny",
                observed=observed,
            )
        )

    return records


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    baselines: dict[str, dict[str, float | int]] = {}
    for baseline in sorted({str(record["baseline"]) for record in records}):
        group = [record for record in records if record["baseline"] == baseline]
        attack = [record for record in group if record["expected"] == "deny"]
        controls = [record for record in group if record["expected"] == "allow"]
        attack_successes = sum(int(record["metrics"]["attack_success"]) for record in attack)
        authorized_successes = sum(
            int(record["metrics"]["authorized_success"]) for record in controls
        )
        correct = sum(int(record["metrics"]["policy_correct"]) for record in group)
        baselines[baseline] = {
            "cases": len(group),
            "attack_cases": len(attack),
            "attack_success_rate": round(attack_successes / len(attack), 6) if attack else 0.0,
            "authorized_controls": len(controls),
            "authorized_success_rate": (
                round(authorized_successes / len(controls), 6) if controls else 0.0
            ),
            "policy_accuracy": round(correct / len(group), 6) if group else 0.0,
        }
    return {
        "schema_version": 1,
        "baselines": baselines,
        "note": (
            "These deterministic synthetic attacks exercise the implemented release boundary. "
            "They are development/research evidence, not a formal security proof."
        ),
    }


def write_outputs(records: list[dict[str, object]], out_dir: str | Path) -> dict[str, object]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "release-boundary-runs.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary = summarize(records)
    (out / "release-boundary-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Long Gate release-boundary red-team cases.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    records = run_release_boundary_redteam()
    summary = write_outputs(records, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
