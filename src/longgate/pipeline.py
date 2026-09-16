from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .audit import audit_dataset
from .backends import get_backend
from .egress import stage_egress
from .inspect import profile_dataframe
from .io import load_table, save_table
from .pii import scan_dataframe_values
from .policy import PolicyEngine
from .profiles import get_profile
from .provenance import build_provenance
from .report import build_report
from .types import DataClass, ReleaseClass
from .utils import sha256_file, utc_now, write_json


@dataclass
class RunResult:
    run_id: str
    out_dir: Path
    report_path: Path
    synthetic_path: Path
    staged_payload: Path | None
    provenance_path: Path
    status: str


def run_pipeline(
    input_path: str | Path,
    out_root: str | Path = "./longgate-runs",
    backend_name: str = "auto",
    seed: int = 42,
    privacy_profile: str = "research",
) -> RunResult:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(
            input_path
        )

    policy_profile = get_profile(
        privacy_profile
    )
    run_id = (
        f"LG-{uuid.uuid4().hex[:12]}"
    )
    out_dir = (
        Path(out_root).resolve()
        / run_id
    )
    safe_dir = out_dir / "safe"
    report_dir = out_dir / "report"
    safe_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    events: list[dict[str, str]] = []

    def event(
        name: str,
        detail: str,
    ) -> None:
        events.append(
            {
                "time": utc_now(),
                "name": name,
                "detail": detail,
            }
        )

    event(
        "Run started",
        (
            "Trusted local pipeline initialized; "
            "network transmission is disabled."
        ),
    )
    event(
        "Privacy profile selected",
        (
            f"{policy_profile.name}: "
            f"min_n={policy_profile.min_dataset_size}, "
            f"min_group={policy_profile.min_group_size}, "
            f"rare_k={policy_profile.rare_k}."
        ),
    )

    input_hash = sha256_file(
        input_path
    )
    event(
        "Source registered",
        (
            "Input SHA-256 recorded; "
            "source row values are not written "
            "to the report."
        ),
    )

    df = load_table(input_path)
    event(
        "Table loaded",
        (
            f"Loaded {len(df)} rows and "
            f"{len(df.columns)} columns locally."
        ),
    )

    profiles = profile_dataframe(df)
    event(
        "Schema classified",
        "Columns classified locally by privacy role.",
    )

    source_pii = scan_dataframe_values(
        df
    )
    event(
        "Value-level PII scan completed",
        (
            f"Detected {source_pii.total_hits} "
            "direct-PII pattern hit(s) locally; "
            "only counts are recorded."
        ),
    )

    backend = get_backend(
        backend_name
    )
    synthetic = backend.generate(
        df,
        profiles,
        seed=seed,
    )
    event(
        "Synthetic data generated",
        (
            f"Backend={backend.name}; direct identifiers "
            "are handled outside model training "
            "where supported."
        ),
    )

    synthetic_path = (
        safe_dir / "synthetic.csv"
    )
    save_table(
        synthetic,
        synthetic_path,
    )
    event(
        "Synthetic artifact staged locally",
        "Synthetic table written to the local safe workspace.",
    )

    audit = audit_dataset(
        df,
        synthetic,
        profiles,
        backend.certified_for_egress,
        privacy_profile=policy_profile,
    )
    event(
        "Privacy audit completed",
        (
            "PASS"
            if audit.passed
            else "BLOCKED: "
            + "; ".join(audit.reasons)
        ),
    )

    decision = PolicyEngine().decide(
        ReleaseClass.SYNTHETIC,
        audit,
    )
    event(
        "Policy evaluated",
        (
            f"allow={decision.allow}; "
            f"{decision.reason}"
        ),
    )

    identifier_columns = [
        profile.name
        for profile in profiles
        if profile.data_class
        == DataClass.IDENTIFIER
    ]
    outbound = synthetic.drop(
        columns=identifier_columns,
        errors="ignore",
    )
    event(
        "Direct identifiers removed from outbound view",
        (
            f"Dropped {len(identifier_columns)} "
            "identifier column(s) before final egress scan."
        ),
    )

    staged_payload, egress_scan = stage_egress(
        outbound,
        out_dir,
        decision,
    )
    if staged_payload:
        event(
            "Final egress scan passed",
            (
                "No direct-PII pattern was detected "
                "in the outbound payload; "
                "payload staged locally only."
            ),
        )
    elif (
        decision.allow
        and not egress_scan["passed"]
    ):
        event(
            "Final egress scan blocked release",
            (
                f"Detected {egress_scan['pii_hits']} "
                "direct-PII pattern hit(s); "
                "no payload created."
            ),
        )
    else:
        event(
            "Egress blocked",
            "No network-eligible payload was created.",
        )

    effective_allow = (
        staged_payload is not None
    )
    status = (
        "PASS"
        if effective_allow
        else "BLOCKED"
    )

    manifest = {
        "run_id": run_id,
        "version": __version__,
        "privacy_profile": (
            policy_profile.to_dict()
        ),
        "input": {
            "filename": input_path.name,
            "sha256": input_hash,
            "rows": len(df),
            "columns": len(df.columns),
        },
        "source_pii_scan": (
            source_pii.to_dict()
        ),
        "backend": backend.name,
        "backend_certified_for_egress": (
            backend.certified_for_egress
        ),
        "profiles": [
            profile.to_dict()
            for profile in profiles
        ],
        "audit": audit.to_dict(),
        "decision": decision.to_dict(),
        "outbound_identifier_columns_removed": (
            identifier_columns
        ),
        "egress_scan": egress_scan,
        "effective_allow": effective_allow,
        "events": events,
        "network": {
            "cloud_client_loaded": False,
            "network_transmission_performed": False,
            "note": (
                "Pre-1.0 pipeline may stage an eligible "
                "artifact but never sends it."
            ),
        },
    }
    write_json(
        out_dir / "manifest.json",
        manifest,
    )
    write_json(
        out_dir / "audit.json",
        audit.to_dict(),
    )

    report_data = {
        "status": status,
        "rows": len(df),
        "columns": len(df.columns),
        "backend": backend.name,
        "privacy_profile": (
            policy_profile.to_dict()
        ),
        "profiles": [
            profile.to_dict()
            for profile in profiles
        ],
        "audit": audit.to_dict(),
        "decision": decision.to_dict(),
        "source_pii_scan": (
            source_pii.to_dict()
        ),
        "identifier_columns_removed": (
            identifier_columns
        ),
        "egress_scan": egress_scan,
        "events": events,
        "run_id": run_id,
        "input_sha256": input_hash,
        "version": __version__,
    }
    report_path = (
        report_dir
        / "trust-report.html"
    )
    build_report(
        report_data,
        report_path,
    )

    provenance_path = build_provenance(
        out_dir
    )
    event(
        "Provenance sealed",
        (
            "Artifact SHA-256 manifest written. "
            "This is integrity verification, not a digital signature."
        ),
    )

    return RunResult(
        run_id=run_id,
        out_dir=out_dir,
        report_path=report_path,
        synthetic_path=synthetic_path,
        staged_payload=staged_payload,
        provenance_path=provenance_path,
        status=status,
    )
