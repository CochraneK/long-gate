import pandas as pd
import pytest

from longgate.inspect import profile_dataframe
from longgate.r_executor import (
    RUnavailable,
    _friendly_r_term,
    r_describe,
    r_ols,
)


def test_r_friendly_term_maps_safe_aliases():
    aliases = {
        "x0": "age",
        "x1": "group",
    }
    assert (
        _friendly_r_term(
            "(Intercept)",
            aliases,
        )
        == "const"
    )
    assert (
        _friendly_r_term(
            "x0",
            aliases,
        )
        == "age"
    )
    assert (
        _friendly_r_term(
            "x1B",
            aliases,
        )
        == "group[B]"
    )


def test_r_describe_blocks_small_dataset_before_execution():
    df = pd.DataFrame(
        {
            "score": [1.0, 2.0, 3.0],
        }
    )
    profiles = profile_dataframe(df)
    with pytest.raises(ValueError):
        r_describe(
            df,
            profiles,
            min_dataset_size=10,
        )


def test_r_ols_blocks_identifier_predictor_before_execution():
    df = pd.DataFrame(
        {
            "participant_id": list(
                range(20)
            ),
            "score": [
                float(index)
                for index in range(20)
            ],
        }
    )
    profiles = profile_dataframe(df)
    with pytest.raises(ValueError):
        r_ols(
            df,
            profiles,
            "score",
            ["participant_id"],
        )


def test_r_describe_reports_missing_rscript(monkeypatch):
    df = pd.DataFrame(
        {
            "score": [
                float(index)
                for index in range(10)
            ],
        }
    )
    profiles = profile_dataframe(df)
    monkeypatch.setattr(
        "longgate.r_executor.shutil.which",
        lambda _name: None,
    )
    with pytest.raises(RUnavailable):
        r_describe(
            df,
            profiles,
            min_dataset_size=10,
        )
