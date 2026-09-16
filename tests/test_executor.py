import pandas as pd
import pytest

from longgate.executor import describe_numeric, group_summary
from longgate.inspect import profile_dataframe


def test_identifier_numeric_column_excluded_from_describe():
    df = pd.DataFrame(
        {
            "participant_id": list(range(10001, 10011)),
            "score": [float(i) for i in range(10)],
        }
    )
    profiles = profile_dataframe(df)
    result = describe_numeric(df, profiles)
    assert "participant_id" not in result["columns"]
    assert "score" in result["columns"]


def test_small_dataset_describe_is_blocked():
    df = pd.DataFrame(
        {
            "participant_id": [1, 2, 3],
            "score": [1.0, 2.0, 3.0],
        }
    )
    profiles = profile_dataframe(df)
    with pytest.raises(ValueError):
        describe_numeric(df, profiles)


def test_small_groups_are_suppressed():
    df = pd.DataFrame(
        {
            "group": ["A"] * 4 + ["B"] * 6,
            "score": list(range(10)),
        }
    )
    profiles = profile_dataframe(df)
    result = group_summary(
        df,
        profiles,
        "group",
        "score",
        min_group_size=5,
    )
    assert [g["group"] for g in result["groups"]] == ["B"]


def test_identifier_cannot_be_grouped():
    df = pd.DataFrame(
        {
            "subject_id": [1, 2, 3, 4, 5],
            "score": [1, 2, 3, 4, 5],
        }
    )
    profiles = profile_dataframe(df)
    with pytest.raises(ValueError):
        group_summary(
            df,
            profiles,
            "subject_id",
            "score",
        )
