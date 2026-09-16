from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

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


@dataclass(frozen=True)
class AttributeInferenceDiagnostic:
    target_rows: int
    covered_rows: int
    coverage: float
    correct_predictions: int
    attack_accuracy: float | None
    baseline_accuracy: float
    accuracy_uplift: float | None
    quasi_columns: list[str]
    sensitive_column: str
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LongitudinalLinkageDiagnostic:
    source_rows: int
    later_rows: int
    uniquely_linkable_rows: int
    unique_linkage_rate: float
    correct_unique_links: int
    unique_link_precision: float | None
    quasi_columns: list[str]
    interpretation: str

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


def attribute_inference_diagnostic(
    synthetic: pd.DataFrame,
    target: pd.DataFrame,
    quasi_columns: list[str],
    sensitive_column: str,
) -> AttributeInferenceDiagnostic:
    """Infer a categorical sensitive value from quasi identifiers."""
    if not quasi_columns:
        raise ValueError("At least one quasi-identifier column is required.")
    required = [*quasi_columns, sensitive_column]
    missing = [
        column
        for column in required
        if column not in synthetic.columns
        or column not in target.columns
    ]
    if missing:
        raise KeyError(
            "Missing attribute-inference columns: "
            f"{sorted(set(missing))}"
        )
    if len(target) == 0:
        raise ValueError("Attribute inference requires a non-empty target dataset.")

    syn = synthetic[required].copy()
    tgt = target[required].copy()
    for column in required:
        syn[column] = syn[column].fillna("<NA>").astype(str)
        tgt[column] = tgt[column].fillna("<NA>").astype(str)

    global_counts = syn[sensitive_column].value_counts()
    if global_counts.empty:
        raise ValueError("Synthetic sensitive column has no usable values.")
    baseline_label = str(global_counts.index[0])
    baseline_accuracy = float(
        (tgt[sensitive_column] == baseline_label).mean()
    )

    mapping: dict[tuple[str, ...], str] = {}
    grouped = syn.groupby(quasi_columns, dropna=False, sort=False)
    for key, part in grouped:
        key_tuple = key if isinstance(key, tuple) else (key,)
        counts = part[sensitive_column].value_counts()
        if not counts.empty:
            mapping[tuple(str(v) for v in key_tuple)] = str(counts.index[0])

    covered = 0
    correct = 0
    for row in tgt.itertuples(index=False, name=None):
        row_map = dict(zip(required, row))
        key = tuple(str(row_map[column]) for column in quasi_columns)
        prediction = mapping.get(key)
        if prediction is None:
            continue
        covered += 1
        if prediction == str(row_map[sensitive_column]):
            correct += 1

    coverage = covered / len(tgt)
    accuracy = correct / covered if covered else None
    uplift = (
        accuracy - baseline_accuracy
        if accuracy is not None
        else None
    )
    if accuracy is None:
        interpretation = "no covered target rows"
    elif uplift >= 0.2 and coverage >= 0.2:
        interpretation = "material attribute-inference signal for this attack"
    elif uplift > 0:
        interpretation = "some attribute-inference signal for this attack"
    else:
        interpretation = "no improvement over the modal baseline for this attack"

    return AttributeInferenceDiagnostic(
        target_rows=len(tgt),
        covered_rows=covered,
        coverage=round(float(coverage), 6),
        correct_predictions=correct,
        attack_accuracy=None if accuracy is None else round(float(accuracy), 6),
        baseline_accuracy=round(baseline_accuracy, 6),
        accuracy_uplift=None if uplift is None else round(float(uplift), 6),
        quasi_columns=quasi_columns,
        sensitive_column=sensitive_column,
        interpretation=interpretation,
    )


def longitudinal_linkage_diagnostic(
    earlier: pd.DataFrame,
    later: pd.DataFrame,
    quasi_columns: list[str],
    entity_column: str,
) -> LongitudinalLinkageDiagnostic:
    """Test exact cross-time linkage on quasi identifiers."""
    if not quasi_columns:
        raise ValueError("At least one quasi-identifier column is required.")
    required = [*quasi_columns, entity_column]
    missing = [
        column
        for column in required
        if column not in earlier.columns
        or column not in later.columns
    ]
    if missing:
        raise KeyError(
            "Missing longitudinal-linkage columns: "
            f"{sorted(set(missing))}"
        )
    if len(earlier) == 0 or len(later) == 0:
        raise ValueError("Longitudinal linkage requires non-empty snapshots.")

    later_lookup: dict[tuple[str, ...], list[str]] = {}
    for row in (
        later[required]
        .fillna("<NA>")
        .astype(str)
        .itertuples(index=False, name=None)
    ):
        row_map = dict(zip(required, row))
        key = tuple(row_map[column] for column in quasi_columns)
        later_lookup.setdefault(key, []).append(row_map[entity_column])

    unique = 0
    correct = 0
    for row in (
        earlier[required]
        .fillna("<NA>")
        .astype(str)
        .itertuples(index=False, name=None)
    ):
        row_map = dict(zip(required, row))
        key = tuple(row_map[column] for column in quasi_columns)
        candidates = later_lookup.get(key, [])
        if len(candidates) != 1:
            continue
        unique += 1
        if candidates[0] == row_map[entity_column]:
            correct += 1

    linkage_rate = unique / len(earlier)
    precision = correct / unique if unique else None
    if precision is not None and precision >= 0.8 and linkage_rate >= 0.2:
        interpretation = "elevated cross-time linkage for this exact attack"
    elif unique:
        interpretation = "some cross-time linkage for this exact attack"
    else:
        interpretation = "no unique cross-time linkage for this exact attack"

    return LongitudinalLinkageDiagnostic(
        source_rows=len(earlier),
        later_rows=len(later),
        uniquely_linkable_rows=unique,
        unique_linkage_rate=round(float(linkage_rate), 6),
        correct_unique_links=correct,
        unique_link_precision=None if precision is None else round(float(precision), 6),
        quasi_columns=quasi_columns,
        interpretation=interpretation,
    )



@dataclass(frozen=True)
class EnsembleMembershipDiagnostic:
    attacks_run: int
    max_auc: float
    median_auc: float
    best_columns: list[str]
    attack_results: list[dict[str, object]]
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FuzzyLongitudinalLinkageDiagnostic:
    source_rows: int
    later_rows: int
    uniquely_linkable_rows: int
    unique_linkage_rate: float
    correct_unique_links: int
    unique_link_precision: float | None
    categorical_columns: list[str]
    numeric_tolerances: dict[str, float]
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def ensemble_membership_diagnostic(
    members: pd.DataFrame,
    holdout: pd.DataFrame,
    synthetic: pd.DataFrame,
    columns: list[str],
    max_subset_size: int = 2,
    max_attacks: int = 32,
) -> EnsembleMembershipDiagnostic:
    """Run a bounded ensemble of nearest-distance membership attacks.

    The ensemble evaluates single-column and small-subset attacks plus the full
    supplied column set. Reporting the strongest observed AUC is deliberately
    conservative; it is still not a general membership-privacy guarantee.
    """
    unique_columns = list(dict.fromkeys(columns))
    if not unique_columns:
        raise ValueError("At least one numeric column is required.")
    if max_subset_size < 1:
        raise ValueError("max_subset_size must be at least 1.")
    if max_attacks < 1:
        raise ValueError("max_attacks must be at least 1.")

    missing = [
        column
        for column in unique_columns
        if column not in members.columns
        or column not in holdout.columns
        or column not in synthetic.columns
    ]
    if missing:
        raise KeyError(f"Missing membership columns: {missing}")

    candidates: list[tuple[str, ...]] = []
    upper = min(max_subset_size, len(unique_columns))
    for size in range(1, upper + 1):
        candidates.extend(combinations(unique_columns, size))
    full = tuple(unique_columns)
    if full not in candidates:
        candidates.append(full)
    if len(candidates) > max_attacks:
        # Preserve single-column attacks and the full attack, then take
        # deterministic early combinations within the configured budget.
        singles = [item for item in candidates if len(item) == 1]
        middle = [item for item in candidates if len(item) > 1 and item != full]
        budget = max(0, max_attacks - len(singles) - 1)
        candidates = [*singles, *middle[:budget], full]
        candidates = candidates[:max_attacks]

    results: list[dict[str, object]] = []
    for subset in candidates:
        result = distance_membership_diagnostic(
            members,
            holdout,
            synthetic,
            list(subset),
        )
        results.append(
            {
                "columns": list(subset),
                "auc": result.auc,
                "interpretation": result.interpretation,
            }
        )

    aucs = np.asarray([float(item["auc"]) for item in results], dtype=float)
    best_index = int(np.argmax(aucs))
    max_auc = float(aucs[best_index])
    if max_auc >= 0.7:
        interpretation = "elevated signal in at least one ensemble attack"
    elif max_auc >= 0.6:
        interpretation = "above-chance signal in at least one ensemble attack"
    else:
        interpretation = "all evaluated ensemble attacks are near chance"

    return EnsembleMembershipDiagnostic(
        attacks_run=len(results),
        max_auc=round(max_auc, 6),
        median_auc=round(float(np.median(aucs)), 6),
        best_columns=list(results[best_index]["columns"]),
        attack_results=results,
        interpretation=interpretation,
    )


def fuzzy_longitudinal_linkage_diagnostic(
    earlier: pd.DataFrame,
    later: pd.DataFrame,
    categorical_columns: list[str],
    numeric_tolerances: dict[str, float],
    entity_column: str,
) -> FuzzyLongitudinalLinkageDiagnostic:
    """Test bounded fuzzy cross-time linkage without emitting entity values.

    Categorical quasi-identifiers must match exactly after string
    normalization. Numeric quasi-identifiers may drift within explicit
    per-column tolerances.
    """
    if not categorical_columns and not numeric_tolerances:
        raise ValueError(
            "At least one categorical or numeric quasi-identifier is required."
        )
    for column, tolerance in numeric_tolerances.items():
        if isinstance(tolerance, bool) or float(tolerance) < 0:
            raise ValueError(
                f"Tolerance for {column!r} must be a non-negative number."
            )

    required = [
        *categorical_columns,
        *numeric_tolerances.keys(),
        entity_column,
    ]
    missing = [
        column
        for column in required
        if column not in earlier.columns or column not in later.columns
    ]
    if missing:
        raise KeyError(
            "Missing fuzzy longitudinal-linkage columns: "
            f"{sorted(set(missing))}"
        )
    if len(earlier) == 0 or len(later) == 0:
        raise ValueError("Fuzzy longitudinal linkage requires non-empty snapshots.")

    later_categorical = {
        column: later[column].fillna("<NA>").astype(str)
        for column in categorical_columns
    }
    later_numeric = {
        column: pd.to_numeric(later[column], errors="coerce")
        for column in numeric_tolerances
    }

    unique = 0
    correct = 0
    for _, row in earlier[required].iterrows():
        mask = pd.Series(True, index=later.index)
        for column in categorical_columns:
            value = "<NA>" if pd.isna(row[column]) else str(row[column])
            mask &= later_categorical[column] == value
        for column, tolerance in numeric_tolerances.items():
            value = pd.to_numeric(
                pd.Series([row[column]]),
                errors="coerce",
            ).iloc[0]
            if pd.isna(value):
                mask &= False
                continue
            mask &= (later_numeric[column] - float(value)).abs() <= float(tolerance)

        candidates = later.loc[mask, entity_column]
        if len(candidates) != 1:
            continue
        unique += 1
        candidate = candidates.iloc[0]
        if str(candidate) == str(row[entity_column]):
            correct += 1

    linkage_rate = unique / len(earlier)
    precision = correct / unique if unique else None
    if precision is not None and precision >= 0.8 and linkage_rate >= 0.2:
        interpretation = "elevated cross-time linkage for this fuzzy attack"
    elif unique:
        interpretation = "some cross-time linkage for this fuzzy attack"
    else:
        interpretation = "no unique cross-time linkage for this fuzzy attack"

    return FuzzyLongitudinalLinkageDiagnostic(
        source_rows=len(earlier),
        later_rows=len(later),
        uniquely_linkable_rows=unique,
        unique_linkage_rate=round(float(linkage_rate), 6),
        correct_unique_links=correct,
        unique_link_precision=(
            None if precision is None else round(float(precision), 6)
        ),
        categorical_columns=categorical_columns,
        numeric_tolerances={
            column: float(value)
            for column, value in numeric_tolerances.items()
        },
        interpretation=interpretation,
    )
