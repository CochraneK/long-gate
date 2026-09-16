from __future__ import annotations

import pytest

from longgate.release_criteria import (
    RowLevelReleaseEvidence,
    evaluate_row_level_release,
    evidence_from_mapping,
)


def _passing_evidence() -> RowLevelReleaseEvidence:
    return RowLevelReleaseEvidence(
        backend_approved=True,
        direct_pii_hits=0,
        exact_row_overlap=0,
        identifier_overlap=0,
        rare_quasi_overlap=0,
        near_copy_rate=0.001,
        membership_max_auc=0.55,
        attribute_inference_uplift=0.02,
        longitudinal_linkage_rate=0.01,
        benchmark_reproducible=True,
        policy_reviewed=True,
        human_review_recorded=True,
    )


def test_row_level_criteria_never_auto_authorize_release():
    result = evaluate_row_level_release(_passing_evidence())
    assert result.criteria_satisfied is True
    assert result.release_allowed is False
    assert result.next_action == "future_manual_policy_decision"


def test_row_level_criteria_fail_closed_on_missing_attack_evidence():
    evidence = _passing_evidence()
    incomplete = RowLevelReleaseEvidence(
        **{
            **evidence.to_dict(),
            "membership_max_auc": None,
            "attribute_inference_uplift": None,
        }
    )
    result = evaluate_row_level_release(incomplete)
    assert result.criteria_satisfied is False
    assert "membership_evidence_missing" in result.failed_conditions
    assert "attribute_inference_evidence_missing" in result.failed_conditions
    assert result.release_allowed is False


def test_row_level_criteria_detect_attack_signals():
    evidence = RowLevelReleaseEvidence(
        **{
            **_passing_evidence().to_dict(),
            "near_copy_rate": 0.2,
            "membership_max_auc": 0.8,
            "attribute_inference_uplift": 0.4,
            "longitudinal_linkage_rate": 0.5,
        }
    )
    result = evaluate_row_level_release(evidence)
    assert {
        "near_copy_rate",
        "membership_attack_signal",
        "attribute_inference_signal",
        "longitudinal_linkage_signal",
    }.issubset(result.failed_conditions)


def test_evidence_mapping_rejects_schema_drift():
    data = _passing_evidence().to_dict()
    data["mystery"] = True
    with pytest.raises(ValueError, match="unknown fields"):
        evidence_from_mapping(data)



def test_evidence_mapping_rejects_string_boolean():
    data = _passing_evidence().to_dict()
    data["backend_approved"] = "false"
    with pytest.raises(ValueError, match="must be boolean"):
        evidence_from_mapping(data)


def test_evidence_mapping_rejects_negative_count():
    data = _passing_evidence().to_dict()
    data["direct_pii_hits"] = -1
    with pytest.raises(ValueError, match="non-negative integer"):
        evidence_from_mapping(data)


def test_evidence_mapping_rejects_out_of_range_auc():
    data = _passing_evidence().to_dict()
    data["membership_max_auc"] = 1.2
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        evidence_from_mapping(data)


def test_evidence_mapping_allows_negative_attribute_uplift():
    data = _passing_evidence().to_dict()
    data["attribute_inference_uplift"] = -0.2
    evidence = evidence_from_mapping(data)
    assert evidence.attribute_inference_uplift == pytest.approx(-0.2)



def test_release_thresholds_reject_out_of_range_values():
    with pytest.raises(ValueError, match="between 0 and 1"):
        evaluate_row_level_release(
            _passing_evidence(),
            max_membership_auc=1.5,
        )
