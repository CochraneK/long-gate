from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pandas as pd

from .profiles import PrivacyProfile, get_profile
from .types import AuditResult, ColumnProfile, DataClass


def _row_hashes(df: pd.DataFrame) -> set[str]:
    hashes: set[str] = set()
    for _, row in df.iterrows():
        payload = json.dumps(
            [None if pd.isna(v) else str(v) for v in row.tolist()],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        hashes.add(hashlib.sha256(payload.encode("utf-8")).hexdigest())
    return hashes


def _identifier_overlap(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> int:
    overlap = 0
    for profile in profiles:
        if (
            profile.data_class != DataClass.IDENTIFIER
            or profile.name not in raw.columns
            or profile.name not in syn.columns
        ):
            continue
        overlap += len(
            set(raw[profile.name].dropna().astype(str))
            & set(syn[profile.name].dropna().astype(str))
        )
    return overlap


def _quasi_columns(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> list[str]:
    return [
        profile.name
        for profile in profiles
        if profile.data_class == DataClass.QUASI_IDENTIFIER
        and profile.name in raw.columns
        and profile.name in syn.columns
    ]


def _quasi_combo_overlap(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> int:
    cols = _quasi_columns(raw, syn, profiles)
    if not cols:
        return 0
    raw_combos = set(
        map(
            tuple,
            raw[cols].fillna("<NA>").astype(str).to_numpy(),
        )
    )
    syn_combos = set(
        map(
            tuple,
            syn[cols].fillna("<NA>").astype(str).to_numpy(),
        )
    )
    return len(raw_combos & syn_combos)


def _rare_quasi_overlap(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    k: int,
) -> int:
    cols = _quasi_columns(raw, syn, profiles)
    if not cols:
        return 0

    raw_tuples = [
        tuple(row)
        for row in raw[cols]
        .fillna("<NA>")
        .astype(str)
        .to_numpy()
    ]
    counts: dict[tuple[str, ...], int] = {}
    for combo in raw_tuples:
        counts[combo] = counts.get(combo, 0) + 1

    rare = {
        combo
        for combo, count in counts.items()
        if count < k
    }
    syn_combos = {
        tuple(row)
        for row in syn[cols]
        .fillna("<NA>")
        .astype(str)
        .to_numpy()
    }
    return len(rare & syn_combos)


def _near_copy_rate(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    max_rows: int = 400,
) -> float | None:
    cols = [
        profile.name
        for profile in profiles
        if profile.name in raw.columns
        and profile.name in syn.columns
        and profile.data_class != DataClass.IDENTIFIER
        and pd.api.types.is_numeric_dtype(raw[profile.name])
        and pd.api.types.is_numeric_dtype(syn[profile.name])
    ]
    if not cols:
        return None

    real = raw[cols].apply(pd.to_numeric, errors="coerce")
    generated = syn[cols].apply(pd.to_numeric, errors="coerce")
    median = real.median(numeric_only=True)
    real = real.fillna(median)
    generated = generated.fillna(median)
    std = real.std(ddof=0).replace(0, 1.0)
    mean = real.mean()
    real = (real - mean) / std
    generated = (generated - mean) / std

    if len(real) > max_rows:
        real = real.sample(max_rows, random_state=0)
    if len(generated) > max_rows:
        generated = generated.sample(max_rows, random_state=1)

    real_array = real.to_numpy(dtype=float)
    generated_array = generated.to_numpy(dtype=float)
    if real_array.size == 0 or generated_array.size == 0:
        return None

    near = 0
    threshold = max(
        math.sqrt(len(cols)) * 0.05,
        0.05,
    )
    for row in generated_array:
        distance = np.linalg.norm(
            real_array - row,
            axis=1,
        ).min()
        if float(distance) < threshold:
            near += 1
    return round(near / len(generated_array), 6)


def audit_dataset(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    backend_certified: bool,
    privacy_profile: PrivacyProfile | None = None,
) -> AuditResult:
    policy = privacy_profile or get_profile("research")
    common = [
        column
        for column in raw.columns
        if column in syn.columns
    ]
    raw_aligned = raw[common].copy()
    syn_aligned = syn[common].copy()

    exact_rows = len(
        _row_hashes(raw_aligned)
        & _row_hashes(syn_aligned)
    )
    id_overlap = _identifier_overlap(
        raw,
        syn,
        profiles,
    )
    quasi_overlap = _quasi_combo_overlap(
        raw,
        syn,
        profiles,
    )
    rare_overlap = _rare_quasi_overlap(
        raw,
        syn,
        profiles,
        k=policy.rare_k,
    )
    near_rate = _near_copy_rate(
        raw,
        syn,
        profiles,
    )
    free_text = [
        profile.name
        for profile in profiles
        if profile.data_class == DataClass.FREE_TEXT
    ]

    reasons: list[str] = []
    reason_codes: list[str] = []
    if not backend_certified:
        reasons.append(
            "Selected synthetic backend is not approved for row-level egress."
        )
        reason_codes.append("backend_not_approved")
    if not policy.row_level_synthetic_egress:
        reasons.append(
            "Row-level synthetic egress is disabled "
            f"under profile {policy.name!r}."
        )
        reason_codes.append("profile_disallows_row_level")
    if exact_rows > 0:
        reasons.append(
            f"Detected {exact_rows} exact row overlap(s) "
            "between source and synthetic data."
        )
        reason_codes.append("exact_row_overlap")
    if id_overlap > 0:
        reasons.append(
            f"Detected {id_overlap} source identifier value(s) "
            "in the synthetic dataset."
        )
        reason_codes.append("identifier_overlap")
    if rare_overlap > 0:
        reasons.append(
            f"Detected {rare_overlap} rare source quasi-identifier "
            "combination(s) reproduced by the synthetic dataset."
        )
        reason_codes.append("rare_quasi_overlap")
    if free_text:
        reasons.append(
            "Free-text columns remain local-only: "
            + ", ".join(free_text)
        )
        reason_codes.append("free_text_present")
    if (
        near_rate is not None
        and near_rate > policy.max_near_copy_rate
    ):
        reasons.append(
            f"Near-copy rate {near_rate:.3%} exceeds "
            f"profile threshold {policy.max_near_copy_rate:.3%}."
        )
        reason_codes.append("near_copy_rate")

    return AuditResult(
        passed=not reasons,
        backend_certified=backend_certified,
        exact_row_overlap=exact_rows,
        identifier_overlap=id_overlap,
        quasi_combo_overlap=quasi_overlap,
        rare_quasi_overlap=rare_overlap,
        near_copy_rate=near_rate,
        free_text_columns=free_text,
        reasons=reasons,
        reason_codes=reason_codes,
    )
