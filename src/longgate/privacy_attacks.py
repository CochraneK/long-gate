from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MembershipDiagnostic:
    auc: float
    member_count: int
    holdout_count: int
    synthetic_count: int
    columns: list[str]
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LinkageDiagnostic:
    target_rows: int
    auxiliary_rows: int
    unique_matches: int
    unique_linkage_rate: float
    quasi_columns: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class KAnonymityDiagnostic:
    rows: int
    k: int
    min_equivalence_class: int
    unique_rows: int
    unique_row_rate: float
    rows_below_k: int
    rows_below_k_rate: float
    equivalence_classes: int
    quasi_columns: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _numeric_matrix(
    df: pd.DataFrame,
    columns: list[str],
    mean: pd.Series,
    std: pd.Series,
) -> np.ndarray:
    values = df[columns].apply(
        pd.to_numeric,
        errors="coerce",
    )
    values = values.fillna(mean)
    return (
        (values - mean) / std
    ).to_numpy(dtype=float)


def _min_distances(
    candidates: np.ndarray,
    synthetic: np.ndarray,
) -> np.ndarray:
    if (
        not len(candidates)
        or not len(synthetic)
    ):
        raise ValueError(
            "Membership diagnostic requires "
            "non-empty datasets."
        )
    distances = []
    for row in candidates:
        distances.append(
            float(
                np.linalg.norm(
                    synthetic - row,
                    axis=1,
                ).min()
            )
        )
    return np.asarray(distances)


def _pairwise_auc(
    member_scores: np.ndarray,
    holdout_scores: np.ndarray,
) -> float:
    wins = 0.0
    total = (
        len(member_scores)
        * len(holdout_scores)
    )
    if total == 0:
        raise ValueError(
            "Membership diagnostic requires "
            "members and holdout rows."
        )
    for member in member_scores:
        wins += float(
            (member > holdout_scores).sum()
        )
        wins += 0.5 * float(
            (member == holdout_scores).sum()
        )
    return wins / total


def distance_membership_diagnostic(
    members: pd.DataFrame,
    holdout: pd.DataFrame,
    synthetic: pd.DataFrame,
    columns: list[str],
) -> MembershipDiagnostic:
    """Nearest-synthetic-row membership diagnostic.

    AUC near 0.5 means this particular distance attack cannot
    distinguish members from holdout rows. It is not a proof of privacy.
    """
    if not columns:
        raise ValueError(
            "At least one numeric column is required."
        )

    combined = pd.concat(
        [
            members[columns],
            holdout[columns],
        ],
        ignore_index=True,
    ).apply(
        pd.to_numeric,
        errors="coerce",
    )
    mean = combined.mean()
    std = (
        combined.std(ddof=0)
        .replace(0, 1.0)
    )

    member_matrix = _numeric_matrix(
        members,
        columns,
        mean,
        std,
    )
    holdout_matrix = _numeric_matrix(
        holdout,
        columns,
        mean,
        std,
    )
    synthetic_matrix = _numeric_matrix(
        synthetic,
        columns,
        mean,
        std,
    )

    member_scores = -_min_distances(
        member_matrix,
        synthetic_matrix,
    )
    holdout_scores = -_min_distances(
        holdout_matrix,
        synthetic_matrix,
    )
    auc = _pairwise_auc(
        member_scores,
        holdout_scores,
    )

    if auc >= 0.7:
        interpretation = (
            "elevated for this distance-based attack"
        )
    elif auc >= 0.6:
        interpretation = (
            "above chance for this distance-based attack"
        )
    else:
        interpretation = (
            "near chance for this distance-based attack"
        )

    return MembershipDiagnostic(
        auc=round(float(auc), 6),
        member_count=len(members),
        holdout_count=len(holdout),
        synthetic_count=len(synthetic),
        columns=columns,
        interpretation=interpretation,
    )


def unique_linkage_diagnostic(
    target: pd.DataFrame,
    auxiliary: pd.DataFrame,
    quasi_columns: list[str],
) -> LinkageDiagnostic:
    """Exact quasi-identifier linkage diagnostic against auxiliary data."""
    if not quasi_columns:
        raise ValueError(
            "At least one quasi-identifier column is required."
        )

    missing = [
        column
        for column in quasi_columns
        if (
            column not in target.columns
            or column not in auxiliary.columns
        )
    ]
    if missing:
        raise KeyError(
            "Missing quasi-identifier columns: "
            f"{missing}"
        )

    aux_counts = (
        auxiliary[quasi_columns]
        .fillna("<NA>")
        .astype(str)
        .value_counts(dropna=False)
        .to_dict()
    )

    unique_matches = 0
    for row in (
        target[quasi_columns]
        .fillna("<NA>")
        .astype(str)
        .itertuples(
            index=False,
            name=None,
        )
    ):
        if aux_counts.get(
            tuple(row),
            0,
        ) == 1:
            unique_matches += 1

    rate = (
        unique_matches / len(target)
        if len(target)
        else 0.0
    )
    return LinkageDiagnostic(
        target_rows=len(target),
        auxiliary_rows=len(auxiliary),
        unique_matches=unique_matches,
        unique_linkage_rate=round(
            rate,
            6,
        ),
        quasi_columns=quasi_columns,
    )


def k_anonymity_diagnostic(
    df: pd.DataFrame,
    quasi_columns: list[str],
    k: int = 5,
) -> KAnonymityDiagnostic:
    """Describe equivalence-class risk for selected quasi-identifiers.

    This is a transparent k-anonymity-style diagnostic. Meeting a chosen
    k threshold is not treated as proof of anonymity, and it does not
    address attribute disclosure, auxiliary data, or semantic linkage.
    """
    if k < 2:
        raise ValueError(
            "k must be at least 2."
        )
    if not quasi_columns:
        raise ValueError(
            "At least one quasi-identifier column is required."
        )

    missing = [
        column
        for column in quasi_columns
        if column not in df.columns
    ]
    if missing:
        raise KeyError(
            "Missing quasi-identifier columns: "
            f"{missing}"
        )

    rows = len(df)
    if rows == 0:
        return KAnonymityDiagnostic(
            rows=0,
            k=k,
            min_equivalence_class=0,
            unique_rows=0,
            unique_row_rate=0.0,
            rows_below_k=0,
            rows_below_k_rate=0.0,
            equivalence_classes=0,
            quasi_columns=quasi_columns,
        )

    counts = (
        df[quasi_columns]
        .fillna("<NA>")
        .astype(str)
        .value_counts(
            dropna=False,
        )
    )
    unique_rows = int(
        counts[counts == 1].sum()
    )
    rows_below_k = int(
        counts[counts < k].sum()
    )

    return KAnonymityDiagnostic(
        rows=rows,
        k=k,
        min_equivalence_class=int(
            counts.min()
        ),
        unique_rows=unique_rows,
        unique_row_rate=round(
            unique_rows / rows,
            6,
        ),
        rows_below_k=rows_below_k,
        rows_below_k_rate=round(
            rows_below_k / rows,
            6,
        ),
        equivalence_classes=len(counts),
        quasi_columns=quasi_columns,
    )
