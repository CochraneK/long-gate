import pytest

from longgate.aggregate_guard import (
    build_release_safe_describe,
    validate_aggregate_payload,
)


def test_aggregate_guard_blocks_pii_in_group_label():
    with pytest.raises(ValueError):
        validate_aggregate_payload(
            {"groups": [{"group": "person@example.com", "n": 10, "mean": 2.0}]}
        )


def test_aggregate_guard_allows_clean_statistics():
    result = {"n": 30, "mean": 2.5, "std": 0.4}
    assert validate_aggregate_payload(result) == result


def test_aggregate_guard_does_not_treat_long_decimal_as_phone():
    payload = {
        "n": 10,
        "mean": 20.9,
        "std": 0.875595035770913,
    }
    assert validate_aggregate_payload(payload) == payload


def test_release_safe_describe_buckets_counts_rounds_and_drops_extrema():
    summary = {
        "n_rows": 13,
        "columns": {
            "score": {
                "n": 13,
                "mean": 2.34567,
                "std": 0.87654,
                "min": 1.0,
                "max": 4.0,
            }
        },
    }
    result = build_release_safe_describe(
        summary,
        min_release_n=10,
        count_bucket_size=5,
    )
    assert result["n_rows_bucket"] == "10-19"
    assert result["columns"]["score"] == {
        "n_bucket": "10-19",
        "mean": 2.35,
        "std": 0.88,
    }
    assert "min" not in result["columns"]["score"]
    assert "max" not in result["columns"]["score"]
    assert "n" not in result["columns"]["score"]
    assert result["disclosure_controls"]["exact_counts_released"] is False
    assert result["disclosure_controls"]["extrema_released"] is False


def test_release_safe_describe_suppresses_sparse_numeric_columns():
    summary = {
        "n_rows": 20,
        "columns": {
            "complete": {
                "n": 20,
                "mean": 10.0,
                "std": 2.0,
                "min": 1.0,
                "max": 20.0,
            },
            "sparse": {
                "n": 4,
                "mean": 99.0,
                "std": 1.0,
                "min": 98.0,
                "max": 100.0,
            },
        },
    }
    result = build_release_safe_describe(
        summary,
        min_release_n=10,
        count_bucket_size=5,
    )
    assert "complete" in result["columns"]
    assert "sparse" not in result["columns"]


def test_release_safe_describe_fails_if_nothing_is_releasable():
    summary = {
        "n_rows": 20,
        "columns": {
            "sparse": {
                "n": 4,
                "mean": 1.0,
                "std": 0.1,
                "min": 0.9,
                "max": 1.1,
            }
        },
    }
    with pytest.raises(ValueError):
        build_release_safe_describe(
            summary,
            min_release_n=10,
            count_bucket_size=5,
        )


def test_aggregate_guard_blocks_pii_in_dictionary_key():
    with pytest.raises(ValueError):
        validate_aggregate_payload(
            {
                "summary": {
                    "person@example.com": {
                        "n_bucket": "10-19",
                        "mean": 2.0,
                        "std": 0.5,
                    }
                }
            }
        )
