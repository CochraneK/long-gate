import pandas as pd
import pytest

from longgate.privacy_attacks import (
    distance_membership_diagnostic,
    k_anonymity_diagnostic,
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
