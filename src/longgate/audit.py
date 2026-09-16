from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pandas as pd

from .types import AuditResult, ColumnProfile, DataClass

K_RARE = 5


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
    for p in profiles:
        if (
            p.data_class != DataClass.IDENTIFIER
            or p.name not in raw.columns
            or p.name not in syn.columns
        ):
            continue
        overlap += len(
            set(raw[p.name].dropna().astype(str)) & set(syn[p.name].dropna().astype(str))
        )
    return overlap


def _quasi_columns(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> list[str]:
    return [
        p.name
        for p in profiles
        if p.data_class == DataClass.QUASI_IDENTIFIER
        and p.name in raw.columns
        and p.name in syn.columns
    ]


def _quasi_combo_overlap(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> int:
    cols = _quasi_columns(raw, syn, profiles)
    if not cols:
        return 0
    raw_combos = set(map(tuple, raw[cols].fillna("<NA>").astype(str).to_numpy()))
    syn_combos = set(map(tuple, syn[cols].fillna("<NA>").astype(str).to_numpy()))
    return len(raw_combos & syn_combos)


def _rare_quasi_overlap(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    k: int = K_RARE,
) -> int:
    cols = _quasi_columns(raw, syn, profiles)
    if not cols:
        return 0

    raw_tuples = [tuple(row) for row in raw[cols].fillna("<NA>").astype(str).to_numpy()]
    counts: dict[tuple[str, ...], int] = {}
    for combo in raw_tuples:
        counts[combo] = counts.get(combo, 0) + 1

    rare = {combo for combo, n in counts.items() if n < k}
    syn_combos = {tuple(row) for row in syn[cols].fillna("<NA>").astype(str).to_numpy()}
    return len(rare & syn_combos)


def _near_copy_rate(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    max_rows: int = 400,
) -> float | None:
    cols = [
        p.name
        for p in profiles
        if p.name in raw.columns
        and p.name in syn.columns
        and p.data_class != DataClass.IDENTIFIER
        and pd.api.types.is_numeric_dtype(raw[p.name])
        and pd.api.types.is_numeric_dtype(syn[p.name])
    ]
    if not cols:
        return None

    r = raw[cols].apply(pd.to_numeric, errors="coerce")
    s = syn[cols].apply(pd.to_numeric, errors="coerce")
    med = r.median(numeric_only=True)
    r = r.fillna(med)
    s = s.fillna(med)
    std = r.std(ddof=0).replace(0, 1.0)
    mean = r.mean()
    r = (r - mean) / std
    s = (s - mean) / std

    if len(r) > max_rows:
        r = r.sample(max_rows, random_state=0)
    if len(s) > max_rows:
        s = s.sample(max_rows, random_state=1)

    ra = r.to_numpy(dtype=float)
    sa = s.to_numpy(dtype=float)
    if ra.size == 0 or sa.size == 0:
        return None

    near = 0
    threshold = max(math.sqrt(len(cols)) * 0.05, 0.05)
    for row in sa:
        if float(np.linalg.norm(ra - row, axis=1).min()) < threshold:
            near += 1
    return round(near / len(sa), 6)


def audit_dataset(
    raw: pd.DataFrame,
    syn: pd.DataFrame,
    profiles: list[ColumnProfile],
    backend_certified: bool,
) -> AuditResult:
    common = [c for c in raw.columns if c in syn.columns]
    raw_aligned = raw[common].copy()
    syn_aligned = syn[common].copy()

    exact_rows = len(_row_hashes(raw_aligned) & _row_hashes(syn_aligned))
    id_overlap = _identifier_overlap(raw, syn, profiles)
    quasi_overlap = _quasi_combo_overlap(raw, syn, profiles)
    rare_overlap = _rare_quasi_overlap(raw, syn, profiles)
    near_rate = _near_copy_rate(raw, syn, profiles)
    free_text = [p.name for p in profiles if p.data_class == DataClass.FREE_TEXT]

    reasons: list[str] = []
    if not backend_certified:
        reasons.append("Selected backend is not approved for row-level egress.")
    if exact_rows > 0:
        reasons.append(
            f"Detected {exact_rows} exact row overlap(s) between source and synthetic data."
        )
    if id_overlap > 0:
        reasons.append(
            f"Detected {id_overlap} source identifier value(s) in the synthetic dataset."
        )
    if rare_overlap > 0:
        reasons.append(
            f"Detected {rare_overlap} rare source quasi-identifier combination(s) "
            "reproduced by the synthetic dataset."
        )
    if free_text:
        reasons.append(
            "Free-text columns are blocked from network release in v0.2: " + ", ".join(free_text)
        )
    if near_rate is not None and near_rate > 0.02:
        reasons.append(f"Near-copy rate {near_rate:.3%} exceeds the v0.2 threshold of 2%.")

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
    )
