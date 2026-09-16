from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RowLevelReleaseEvidence:
    backend_approved: bool
    direct_pii_hits: int
    exact_row_overlap: int
    identifier_overlap: int
    rare_quasi_overlap: int
    near_copy_rate: float | None
    membership_max_auc: float | None
    attribute_inference_uplift: float | None
    longitudinal_linkage_rate: float | None
    benchmark_reproducible: bool
    policy_reviewed: bool
    human_review_recorded: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RowLevelReleaseEvaluation:
    criteria_version: str
    criteria_satisfied: bool
    failed_conditions: list[str]
    release_allowed: bool
    next_action: str
    thresholds: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_row_level_release(
    evidence: RowLevelReleaseEvidence,
    *,
    max_near_copy_rate: float = 0.01,
    max_membership_auc: float = 0.60,
    max_attribute_inference_uplift: float = 0.10,
    max_longitudinal_linkage_rate: float = 0.05,
) -> RowLevelReleaseEvaluation:
    """Evaluate production evidence while preserving the pre-1.0 hard lock.

    This function deliberately cannot authorize row-level synthetic egress.
    It only says whether the minimum evidence package is complete enough for
    a separate human/policy decision in a future release process.
    """
    for name, value in {
        "max_near_copy_rate": max_near_copy_rate,
        "max_membership_auc": max_membership_auc,
        "max_attribute_inference_uplift": max_attribute_inference_uplift,
        "max_longitudinal_linkage_rate": max_longitudinal_linkage_rate,
    }.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be numeric.")
        if not 0 <= float(value) <= 1:
            raise ValueError(f"{name} must be between 0 and 1.")

    thresholds = {
        "max_near_copy_rate": float(max_near_copy_rate),
        "max_membership_auc": float(max_membership_auc),
        "max_attribute_inference_uplift": float(
            max_attribute_inference_uplift
        ),
        "max_longitudinal_linkage_rate": float(
            max_longitudinal_linkage_rate
        ),
    }
    failures: list[str] = []

    if not evidence.backend_approved:
        failures.append("backend_not_approved")
    if evidence.direct_pii_hits != 0:
        failures.append("direct_pii_detected")
    if evidence.exact_row_overlap != 0:
        failures.append("exact_row_overlap")
    if evidence.identifier_overlap != 0:
        failures.append("identifier_overlap")
    if evidence.rare_quasi_overlap != 0:
        failures.append("rare_quasi_overlap")

    if evidence.near_copy_rate is None:
        failures.append("near_copy_evidence_missing")
    elif evidence.near_copy_rate > max_near_copy_rate:
        failures.append("near_copy_rate")

    if evidence.membership_max_auc is None:
        failures.append("membership_evidence_missing")
    elif evidence.membership_max_auc > max_membership_auc:
        failures.append("membership_attack_signal")

    if evidence.attribute_inference_uplift is None:
        failures.append("attribute_inference_evidence_missing")
    elif evidence.attribute_inference_uplift > max_attribute_inference_uplift:
        failures.append("attribute_inference_signal")

    if evidence.longitudinal_linkage_rate is None:
        failures.append("longitudinal_evidence_missing")
    elif evidence.longitudinal_linkage_rate > max_longitudinal_linkage_rate:
        failures.append("longitudinal_linkage_signal")

    if not evidence.benchmark_reproducible:
        failures.append("benchmark_not_reproducible")
    if not evidence.policy_reviewed:
        failures.append("policy_not_reviewed")
    if not evidence.human_review_recorded:
        failures.append("human_review_missing")

    satisfied = not failures
    return RowLevelReleaseEvaluation(
        criteria_version="row-level-release-evidence-v1",
        criteria_satisfied=satisfied,
        failed_conditions=failures,
        release_allowed=False,
        next_action=(
            "future_manual_policy_decision"
            if satisfied
            else "collect_or_improve_evidence"
        ),
        thresholds=thresholds,
    )


def _strict_bool(data: dict[str, object], key: str) -> bool:
    value = data[key]
    if not isinstance(value, bool):
        raise ValueError(f"Row-level evidence {key} must be boolean.")
    return value


def _non_negative_int(data: dict[str, object], key: str) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Row-level evidence {key} must be a non-negative integer."
        )
    return value


def _optional_rate(
    data: dict[str, object],
    key: str,
    *,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float | None:
    value = data[key]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Row-level evidence {key} must be numeric or null.")
    result = float(value)
    if not minimum <= result <= maximum:
        raise ValueError(
            f"Row-level evidence {key} must be between "
            f"{minimum} and {maximum}."
        )
    return result


def evidence_from_mapping(data: dict[str, object]) -> RowLevelReleaseEvidence:
    required = {
        "backend_approved",
        "direct_pii_hits",
        "exact_row_overlap",
        "identifier_overlap",
        "rare_quasi_overlap",
        "near_copy_rate",
        "membership_max_auc",
        "attribute_inference_uplift",
        "longitudinal_linkage_rate",
        "benchmark_reproducible",
        "policy_reviewed",
        "human_review_recorded",
    }
    missing = required - data.keys()
    extra = data.keys() - required
    if missing:
        raise ValueError(f"Row-level evidence missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"Row-level evidence has unknown fields: {sorted(extra)}")
    return RowLevelReleaseEvidence(
        backend_approved=_strict_bool(data, "backend_approved"),
        direct_pii_hits=_non_negative_int(data, "direct_pii_hits"),
        exact_row_overlap=_non_negative_int(data, "exact_row_overlap"),
        identifier_overlap=_non_negative_int(data, "identifier_overlap"),
        rare_quasi_overlap=_non_negative_int(data, "rare_quasi_overlap"),
        near_copy_rate=_optional_rate(data, "near_copy_rate"),
        membership_max_auc=_optional_rate(data, "membership_max_auc"),
        attribute_inference_uplift=_optional_rate(
            data,
            "attribute_inference_uplift",
            minimum=-1.0,
            maximum=1.0,
        ),
        longitudinal_linkage_rate=_optional_rate(
            data,
            "longitudinal_linkage_rate",
        ),
        benchmark_reproducible=_strict_bool(
            data,
            "benchmark_reproducible",
        ),
        policy_reviewed=_strict_bool(data, "policy_reviewed"),
        human_review_recorded=_strict_bool(
            data,
            "human_review_recorded",
        ),
    )
