from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker

from .base import SyntheticBackend
from ..types import ColumnProfile, DataClass


class DemoBackend(SyntheticBackend):
    """Offline demonstration backend; never eligible for egress."""

    name = "demo"
    certified_for_egress = False
    description = "Local demo synthesizer; useful for pipeline tests, never for cloud release."

    def generate(self, df: pd.DataFrame, profiles: list[ColumnProfile], seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        fake = Faker(["en_GB", "zh_CN"])
        fake.seed_instance(seed)
        out = pd.DataFrame(index=range(len(df)))
        by_name = {p.name: p for p in profiles}
        for col in df.columns:
            p = by_name[str(col)]
            s = df[col]
            if p.data_class == DataClass.IDENTIFIER:
                out[col] = [self._fake_identifier(str(col), fake, i, seed) for i in range(len(df))]
                continue
            if pd.api.types.is_numeric_dtype(s):
                clean = pd.to_numeric(s, errors="coerce").dropna()
                if clean.empty:
                    out[col] = np.nan
                    continue
                mean = float(clean.mean())
                std = float(clean.std(ddof=0)) or max(abs(mean) * 0.05, 1.0)
                vals = rng.normal(mean, std, size=len(df))
                lo, hi = float(clean.min()), float(clean.max())
                pad = max((hi - lo) * 0.05, std * 0.05)
                vals = np.clip(vals, lo - pad, hi + pad)
                if pd.api.types.is_integer_dtype(s):
                    vals = np.rint(vals).astype(int)
                out[col] = vals
                continue
            values = s.dropna().astype(str)
            if values.empty:
                out[col] = None
                continue
            counts = values.value_counts(normalize=True)
            probs = counts.to_numpy(dtype=float)
            probs = probs + 1.0 / max(len(values), 1)
            probs = probs / probs.sum()
            out[col] = rng.choice(counts.index.to_numpy(), size=len(df), p=probs)
        return out

    @staticmethod
    def _fake_identifier(col: str, fake: Faker, i: int, seed: int) -> str:
        n = col.lower()
        if "email" in n or "邮箱" in n:
            return f"synthetic-{seed}-{i}@example.invalid"
        if any(k in n for k in ["phone", "mobile", "tel", "手机号", "电话"]):
            return f"+00-000-{(seed + i) % 10000:04d}-{i % 10000:04d}"
        if any(k in n for k in ["address", "postcode", "postal", "zip", "地址", "住址", "邮编"]):
            return f"Synthetic Address {i + 1}"
        if any(k in n for k in ["name", "姓名"]):
            return fake.name()
        return f"SYN-{seed:04d}-{i + 1:06d}"
