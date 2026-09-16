import pytest

from longgate.aggregate_guard import validate_aggregate_payload


def test_aggregate_guard_blocks_pii_in_group_label():
    with pytest.raises(ValueError):
        validate_aggregate_payload(
            {"groups": [{"group": "person@example.com", "n": 10, "mean": 2.0}]}
        )


def test_aggregate_guard_allows_clean_statistics():
    result = {"n": 30, "mean": 2.5, "std": 0.4}
    assert validate_aggregate_payload(result) == result
