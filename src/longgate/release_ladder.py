from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .aggregate_guard import validate_aggregate_payload
from .egress import stage_json_egress
from .executor import describe_numeric
from .policy import PolicyEngine
from .profiles import PrivacyProfile
from .types import AuditResult, ColumnProfile, DataClass, ReleaseClass


@dataclass(frozen=True)
class ReleaseResolution:
    requested_release_class: str
    granted_release_class: str | None
    workflow_status: str
    row_level_release_allowed: bool
    aggregate_fallback_used: bool
    artifact: str | None
    blockers: list[str]
    next_actions: list[str]
    aggregate_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _class_counts(profiles: list[ColumnProfile]) -> dict[str, int]:
    counts = {data_class.value: 0 for data_class in DataClass}
    for profile in profiles:
        counts[profile.data_class.value] += 1
    return counts


def next_actions_for_audit(
    audit: AuditResult,
    profile: PrivacyProfile,
) -> list[str]:
    codes = set(audit.reason_codes)
    actions: list[str] = []

    if "exact_row_overlap" in codes:
        actions.append(
            "Regenerate with a stronger synthesis configuration; exact source-row copies must reach zero."
        )
    if "identifier_overlap" in codes:
        actions.append(
            "Exclude direct identifiers from synthesis training/output and regenerate them independently or remove them."
        )
    if "rare_quasi_overlap" in codes:
        actions.append(
            "Generalize or suppress rare quasi-identifier combinations, then rerun the privacy audit."
        )
    if "near_copy_rate" in codes:
        actions.append(
            "Increase synthesis noise/generalization or use a stronger backend until the near-copy rate is below the profile threshold."
        )
    if "free_text_present" in codes:
        actions.append(
            "Route free-text columns through the local semantic path or remove them from any row-level release candidate."
        )
    if "backend_not_approved" in codes:
        actions.append(
            "Keep row-level synthetic output local until the selected backend has an evidence-backed release profile."
        )
    if "profile_disallows_row_level" in codes:
        actions.append(
            f"Profile {profile.name!r} deliberately disables row-level synthetic egress; use a reviewed organization policy before enabling it."
        )

    actions.append(
        "Continue the workflow with the aggregate fallback when row-level release is not justified."
    )
    return actions


def resolve_release(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    profile: PrivacyProfile,
    audit: AuditResult,
    out_dir: Path,
    row_level_payload: Path | None,
) -> tuple[ReleaseResolution, Path | None, dict[str, object]]:
    if row_level_payload is not None:
        resolution = ReleaseResolution(
            requested_release_class=ReleaseClass.SYNTHETIC.value,
            granted_release_class=ReleaseClass.SYNTHETIC.value,
            workflow_status="READY",
            row_level_release_allowed=True,
            aggregate_fallback_used=False,
            artifact=str(row_level_payload),
            blockers=[],
            next_actions=[],
        )
        return resolution, row_level_payload, {
            "passed": True,
            "pii_hits": 0,
            "by_entity": {},
        }

    blockers = list(audit.reasons)
    next_actions = next_actions_for_audit(audit, profile)

    try:
        summary = describe_numeric(
            df,
            profiles,
            min_dataset_size=profile.min_dataset_size,
        )
        aggregate_payload = {
            "representation": "aggregate_describe",
            "privacy_profile": profile.name,
            "data_class_counts": _class_counts(profiles),
            "summary": summary,
        }
        aggregate_payload = validate_aggregate_payload(
            aggregate_payload
        )
    except (ValueError, TypeError) as exc:
        resolution = ReleaseResolution(
            requested_release_class=ReleaseClass.SYNTHETIC.value,
            granted_release_class=None,
            workflow_status="LOCAL_ONLY",
            row_level_release_allowed=False,
            aggregate_fallback_used=False,
            artifact=None,
            blockers=blockers,
            next_actions=next_actions,
            aggregate_reason=str(exc),
        )
        return resolution, None, {
            "passed": False,
            "pii_hits": 0,
            "by_entity": {},
        }

    aggregate_decision = PolicyEngine().decide(
        ReleaseClass.AGGREGATE
    )
    aggregate_path, aggregate_scan = stage_json_egress(
        aggregate_payload,
        out_dir,
        aggregate_decision,
    )
    if aggregate_path is None:
        resolution = ReleaseResolution(
            requested_release_class=ReleaseClass.SYNTHETIC.value,
            granted_release_class=None,
            workflow_status="LOCAL_ONLY",
            row_level_release_allowed=False,
            aggregate_fallback_used=False,
            artifact=None,
            blockers=blockers,
            next_actions=next_actions,
            aggregate_reason=(
                "Aggregate fallback failed its final egress scan."
            ),
        )
        return resolution, None, aggregate_scan

    resolution = ReleaseResolution(
        requested_release_class=ReleaseClass.SYNTHETIC.value,
        granted_release_class=ReleaseClass.AGGREGATE.value,
        workflow_status="READY",
        row_level_release_allowed=False,
        aggregate_fallback_used=True,
        artifact=str(aggregate_path),
        blockers=blockers,
        next_actions=next_actions,
        aggregate_reason=(
            "Row-level synthetic release was not justified, so Long Gate "
            "continued with an aggregate-only artifact."
        ),
    )
    return resolution, aggregate_path, aggregate_scan
