import pandas as pd
import pytest

from longgate.privacy_attacks import (
    attribute_inference_diagnostic,
    distance_membership_diagnostic,
    k_anonymity_diagnostic,
    longitudinal_linkage_diagnostic,
    unique_linkage_diagnostic,
)


def test_membership_diagnostic_has_bounded_auc():
    members = pd.DataFrame(
        {
            "x": [0.0, 1.0, 2.0],
            "y": [0.0, 1.0, 2.0],
        }
    )
    holdout = pd.DataFrame(
        {
            "x": [10.0, 11.0, 12.0],
            "y": [10.0, 11.0, 12.0],
        }
    )
    synthetic = members.copy()
    result = distance_membership_diagnostic(
        members,
        holdout,
        synthetic,
        ["x", "y"],
    )
    assert 0.0 <= result.auc <= 1.0
    assert result.auc > 0.9


def test_unique_linkage_diagnostic_counts_unique_matches():
    target = pd.DataFrame(
        {
            "age": [20, 21, 22],
            "city": ["A", "B", "C"],
        }
    )
    auxiliary = pd.DataFrame(
        {
            "age": [20, 21, 21, 30],
            "city": ["A", "B", "B", "D"],
        }
    )
    result = unique_linkage_diagnostic(
        target,
        auxiliary,
        ["age", "city"],
    )
    assert result.unique_matches == 1
    assert result.unique_linkage_rate == pytest.approx(
        1 / 3,
        abs=1e-6,
    )


def test_k_anonymity_diagnostic_reports_small_classes():
    df = pd.DataFrame(
        {
            "age": [20, 20, 21, 22, 22, 22],
            "city": ["A", "A", "B", "C", "C", "C"],
        }
    )
    result = k_anonymity_diagnostic(
        df,
        ["age", "city"],
        k=3,
    )
    assert result.rows == 6
    assert result.min_equivalence_class == 1
    assert result.unique_rows == 1
    assert result.rows_below_k == 3
    assert result.rows_below_k_rate == pytest.approx(
        0.5,
        abs=1e-6,
    )


def test_k_anonymity_diagnostic_rejects_invalid_k():
    df = pd.DataFrame(
        {
            "age": [20, 20],
        }
    )
    with pytest.raises(ValueError):
        k_anonymity_diagnostic(
            df,
            ["age"],
            k=1,
        )


def test_attribute_inference_reports_uplift():
    synthetic = pd.DataFrame(
        {
            "age_band": ["20s", "20s", "30s", "30s", "40s", "40s"],
            "city": ["A", "A", "B", "B", "C", "C"],
            "diagnosis": ["x", "x", "y", "y", "z", "z"],
        }
    )
    target = pd.DataFrame(
        {
            "age_band": ["20s", "30s", "40s", "20s", "30s", "40s"],
            "city": ["A", "B", "C", "A", "B", "C"],
            "diagnosis": ["x", "y", "z", "x", "y", "z"],
        }
    )
    result = attribute_inference_diagnostic(
        synthetic,
        target,
        ["age_band", "city"],
        "diagnosis",
    )
    assert result.coverage == 1.0
    assert result.attack_accuracy == 1.0
    assert result.accuracy_uplift is not None
    assert result.accuracy_uplift > 0.5


def test_attribute_inference_reports_no_coverage():
    synthetic = pd.DataFrame(
        {
            "city": ["A", "A"],
            "condition": ["x", "x"],
        }
    )
    target = pd.DataFrame(
        {
            "city": ["B", "C"],
            "condition": ["x", "y"],
        }
    )
    result = attribute_inference_diagnostic(
        synthetic,
        target,
        ["city"],
        "condition",
    )
    assert result.coverage == 0.0
    assert result.attack_accuracy is None


def test_longitudinal_linkage_uses_ground_truth_without_returning_ids():
    earlier = pd.DataFrame(
        {
            "person_id": ["p1", "p2", "p3", "p4"],
            "birth_year": [1990, 1991, 1992, 1993],
            "city": ["A", "B", "C", "D"],
        }
    )
    later = pd.DataFrame(
        {
            "person_id": ["p1", "p2", "p3", "p4"],
            "birth_year": [1990, 1991, 1992, 1993],
            "city": ["A", "B", "C", "D"],
        }
    )
    result = longitudinal_linkage_diagnostic(
        earlier,
        later,
        ["birth_year", "city"],
        "person_id",
    )
    assert result.unique_linkage_rate == 1.0
    assert result.unique_link_precision == 1.0
    payload = str(result.to_dict())
    assert "p1" not in payload
    assert "p2" not in payload


def test_longitudinal_linkage_requires_unique_match():
    earlier = pd.DataFrame(
        {
            "person_id": ["p1", "p2"],
            "city": ["A", "A"],
        }
    )
    later = pd.DataFrame(
        {
            "person_id": ["p1", "p2"],
            "city": ["A", "A"],
        }
    )
    result = longitudinal_linkage_diagnostic(
        earlier,
        later,
        ["city"],
        "person_id",
    )
    assert result.unique_linkage_rate == 0.0
    assert result.unique_link_precision is None
