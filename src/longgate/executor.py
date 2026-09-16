from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .types import ColumnProfile, DataClass


MIN_GROUP_SIZE = 5


def _identifier_columns(profiles: list[ColumnProfile]) -> set[str]:
    return {p.name for p in profiles if p.data_class == DataClass.IDENTIFIER}


def _safe_numeric_columns(df: pd.DataFrame, profiles: list[ColumnProfile]) -> list[str]:
    ids = _identifier_columns(profiles)
    return [c for c in df.columns if c not in ids and pd.api.types.is_numeric_dtype(df[c])]


def describe_numeric(df: pd.DataFrame, profiles: list[ColumnProfile]) -> dict[str, Any]:
    cols = _safe_numeric_columns(df, profiles)
    out: dict[str, Any] = {"n_rows": int(len(df)), "columns": {}}
    for col in cols:
        s = pd.to_numeric(df[col], errors="coerce")
        out["columns"][str(col)] = {
            "n": int(s.notna().sum()),
            "mean": None if s.dropna().empty else float(s.mean()),
            "std": None if s.dropna().empty else float(s.std(ddof=1)),
            "min": None if s.dropna().empty else float(s.min()),
            "max": None if s.dropna().empty else float(s.max()),
        }
    return out


def correlation(df: pd.DataFrame, profiles: list[ColumnProfile]) -> dict[str, Any]:
    cols = _safe_numeric_columns(df, profiles)
    if len(cols) < 2:
        return {"n_rows": int(len(df)), "correlation": {}}
    corr = df[cols].corr(numeric_only=True)
    return {
        "n_rows": int(len(df)),
        "correlation": {
            str(row): {str(col): None if pd.isna(v) else float(v) for col, v in values.items()}
            for row, values in corr.to_dict(orient="index").items()
        },
    }


def group_summary(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    group_by: str,
    value: str,
    min_group_size: int = MIN_GROUP_SIZE,
) -> dict[str, Any]:
    ids = _identifier_columns(profiles)
    if group_by in ids or value in ids:
        raise ValueError("Identifier columns cannot be used in released group summaries.")
    if group_by not in df.columns or value not in df.columns:
        raise KeyError("Unknown group/value column.")
    if not pd.api.types.is_numeric_dtype(df[value]):
        raise TypeError("Group summary value must be numeric.")
    groups = []
    for key, part in df.groupby(group_by, dropna=False):
        n = int(len(part))
        if n < min_group_size:
            continue
        s = pd.to_numeric(part[value], errors="coerce")
        groups.append({
            "group": str(key),
            "n": n,
            "mean": None if s.dropna().empty else float(s.mean()),
            "std": None if s.dropna().empty else float(s.std(ddof=1)),
        })
    return {"group_by": group_by, "value": value, "min_group_size": min_group_size, "groups": groups}


def ols(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    outcome: str,
    predictors: list[str],
) -> dict[str, Any]:
    ids = _identifier_columns(profiles)
    selected = [outcome, *predictors]
    if any(c in ids for c in selected):
        raise ValueError("Identifier columns cannot be used in released regression models.")
    if outcome not in df.columns or any(c not in df.columns for c in predictors):
        raise KeyError("Unknown regression column.")
    if not pd.api.types.is_numeric_dtype(df[outcome]):
        raise TypeError("OLS outcome must be numeric.")
    try:
        import statsmodels.api as sm
    except ImportError as exc:
        raise RuntimeError("OLS requires the optional stats dependency: pip install 'long-gate[stats]'") from exc

    X = pd.DataFrame(index=df.index)
    for col in predictors:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            X[col] = pd.to_numeric(s, errors="coerce")
        else:
            counts = s.astype("string").value_counts(dropna=False)
            if len(counts) > 50 or (counts < MIN_GROUP_SIZE).any():
                raise ValueError(f"Categorical predictor {col!r} has rare/high-cardinality levels.")
            dummies = pd.get_dummies(s.astype("string"), prefix=col, drop_first=True, dtype=float)
            X = pd.concat([X, dummies], axis=1)
    y = pd.to_numeric(df[outcome], errors="coerce")
    model_df = pd.concat([y.rename("__y__"), X], axis=1).dropna()
    if len(model_df) < max(10, len(X.columns) + 3):
        raise ValueError("Too few complete observations for safe released OLS summary.")
    X2 = sm.add_constant(model_df.drop(columns="__y__"), has_constant="add")
    res = sm.OLS(model_df["__y__"], X2).fit()
    ci = res.conf_int()
    terms = {}
    for term in res.params.index:
        terms[str(term)] = {
            "coef": float(res.params[term]),
            "se": float(res.bse[term]),
            "p": float(res.pvalues[term]),
            "ci_low": float(ci.loc[term, 0]),
            "ci_high": float(ci.loc[term, 1]),
        }
    return {
        "model": "OLS",
        "outcome": outcome,
        "predictors": predictors,
        "nobs": int(res.nobs),
        "r_squared": float(res.rsquared),
        "adj_r_squared": float(res.rsquared_adj),
        "terms": terms,
    }
