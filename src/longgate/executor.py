from __future__ import annotations

from typing import Any

import pandas as pd

from .types import ColumnProfile, DataClass

MIN_GROUP_SIZE = 5
MIN_DATASET_SIZE = 10


def _identifier_columns(
    profiles: list[ColumnProfile],
) -> set[str]:
    return {
        profile.name
        for profile in profiles
        if profile.data_class == DataClass.IDENTIFIER
    }


def _safe_numeric_columns(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> list[str]:
    identifiers = _identifier_columns(profiles)
    return [
        column
        for column in df.columns
        if column not in identifiers
        and pd.api.types.is_numeric_dtype(df[column])
    ]


def describe_numeric(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    min_dataset_size: int = MIN_DATASET_SIZE,
) -> dict[str, Any]:
    if len(df) < min_dataset_size:
        raise ValueError(
            "Dataset is too small for released descriptive statistics."
        )

    columns = _safe_numeric_columns(
        df,
        profiles,
    )
    out: dict[str, Any] = {
        "n_rows": len(df),
        "columns": {},
    }
    for column in columns:
        series = pd.to_numeric(
            df[column],
            errors="coerce",
        )
        out["columns"][str(column)] = {
            "n": int(series.notna().sum()),
            "mean": (
                None
                if series.dropna().empty
                else float(series.mean())
            ),
            "std": (
                None
                if series.dropna().empty
                else float(series.std(ddof=1))
            ),
            "min": (
                None
                if series.dropna().empty
                else float(series.min())
            ),
            "max": (
                None
                if series.dropna().empty
                else float(series.max())
            ),
        }
    return out


def correlation(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    min_dataset_size: int = MIN_DATASET_SIZE,
) -> dict[str, Any]:
    if len(df) < min_dataset_size:
        raise ValueError(
            "Dataset is too small for released correlation statistics."
        )

    columns = _safe_numeric_columns(
        df,
        profiles,
    )
    if len(columns) < 2:
        return {
            "n_rows": len(df),
            "correlation": {},
        }

    corr = df[columns].corr(
        numeric_only=True
    )
    return {
        "n_rows": len(df),
        "correlation": {
            str(row): {
                str(column): (
                    None
                    if pd.isna(value)
                    else float(value)
                )
                for column, value in values.items()
            }
            for row, values in corr.to_dict(
                orient="index"
            ).items()
        },
    }


def group_summary(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    group_by: str,
    value: str,
    min_group_size: int = MIN_GROUP_SIZE,
) -> dict[str, Any]:
    identifiers = _identifier_columns(profiles)
    if (
        group_by in identifiers
        or value in identifiers
    ):
        raise ValueError(
            "Identifier columns cannot be used "
            "in released group summaries."
        )
    if (
        group_by not in df.columns
        or value not in df.columns
    ):
        raise KeyError(
            "Unknown group/value column."
        )
    if not pd.api.types.is_numeric_dtype(
        df[value]
    ):
        raise TypeError(
            "Group summary value must be numeric."
        )

    groups = []
    for key, part in df.groupby(
        group_by,
        dropna=False,
    ):
        n = len(part)
        if n < min_group_size:
            continue
        series = pd.to_numeric(
            part[value],
            errors="coerce",
        )
        groups.append(
            {
                "group": str(key),
                "n": n,
                "mean": (
                    None
                    if series.dropna().empty
                    else float(series.mean())
                ),
                "std": (
                    None
                    if series.dropna().empty
                    else float(series.std(ddof=1))
                ),
            }
        )

    return {
        "group_by": group_by,
        "value": value,
        "min_group_size": min_group_size,
        "groups": groups,
    }


def ols(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    outcome: str,
    predictors: list[str],
    min_dataset_size: int = MIN_DATASET_SIZE,
    min_group_size: int = MIN_GROUP_SIZE,
) -> dict[str, Any]:
    identifiers = _identifier_columns(profiles)
    selected = [
        outcome,
        *predictors,
    ]

    if any(
        column in identifiers
        for column in selected
    ):
        raise ValueError(
            "Identifier columns cannot be used "
            "in released regression models."
        )
    if (
        outcome not in df.columns
        or any(
            column not in df.columns
            for column in predictors
        )
    ):
        raise KeyError(
            "Unknown regression column."
        )
    if not pd.api.types.is_numeric_dtype(
        df[outcome]
    ):
        raise TypeError(
            "OLS outcome must be numeric."
        )

    try:
        import statsmodels.api as sm
    except ImportError as exc:
        raise RuntimeError(
            "OLS requires the optional stats dependency: "
            "pip install 'long-gate[stats]'"
        ) from exc

    features = pd.DataFrame(
        index=df.index
    )
    for column in predictors:
        series = df[column]
        if pd.api.types.is_numeric_dtype(
            series
        ):
            features[column] = pd.to_numeric(
                series,
                errors="coerce",
            )
        else:
            counts = (
                series.astype("string")
                .value_counts(dropna=False)
            )
            if (
                len(counts) > 50
                or (counts < min_group_size).any()
            ):
                raise ValueError(
                    f"Categorical predictor {column!r} "
                    "has rare/high-cardinality levels."
                )
            dummies = pd.get_dummies(
                series.astype("string"),
                prefix=column,
                drop_first=True,
                dtype=float,
            )
            features = pd.concat(
                [
                    features,
                    dummies,
                ],
                axis=1,
            )

    target = pd.to_numeric(
        df[outcome],
        errors="coerce",
    )
    model_df = pd.concat(
        [
            target.rename("__y__"),
            features,
        ],
        axis=1,
    ).dropna()

    if len(model_df) < max(
        min_dataset_size,
        len(features.columns) + 3,
    ):
        raise ValueError(
            "Too few complete observations "
            "for safe released OLS summary."
        )

    design = sm.add_constant(
        model_df.drop(
            columns="__y__"
        ),
        has_constant="add",
    )
    result = sm.OLS(
        model_df["__y__"],
        design,
    ).fit()
    confidence = result.conf_int()

    terms = {}
    for term in result.params.index:
        terms[str(term)] = {
            "coef": float(
                result.params[term]
            ),
            "se": float(
                result.bse[term]
            ),
            "p": float(
                result.pvalues[term]
            ),
            "ci_low": float(
                confidence.loc[term, 0]
            ),
            "ci_high": float(
                confidence.loc[term, 1]
            ),
        }

    return {
        "model": "OLS",
        "outcome": outcome,
        "predictors": predictors,
        "nobs": int(result.nobs),
        "r_squared": float(
            result.rsquared
        ),
        "adj_r_squared": float(
            result.rsquared_adj
        ),
        "terms": terms,
    }
