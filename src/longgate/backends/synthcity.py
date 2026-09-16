from __future__ import annotations

import pandas as pd
from faker import Faker

from .base import SyntheticBackend
from ..types import ColumnProfile, DataClass


class SynthCityBackend(SyntheticBackend):
    """Adapter for the Apache-2.0 SynthCity project."""

    name = "synthcity"
    certified_for_egress = True
    description = "SynthCity joint-distribution synthesis with identifier regeneration."

    def __init__(self, plugin: str = "adsgan") -> None:
        self.plugin = plugin

    def generate(self, df: pd.DataFrame, profiles: list[ColumnProfile], seed: int) -> pd.DataFrame:
        try:
            from synthcity.plugins import Plugins
        except ImportError as exc:
            raise RuntimeError("SynthCity backend requested but not installed. Run: pip install 'long-gate[synthcity]'") from exc
        model = Plugins().get(self.plugin)
        model.fit(df)
        generated = model.generate(count=len(df))
        syn = generated.dataframe() if hasattr(generated, "dataframe") else pd.DataFrame(generated)
        syn = syn.reset_index(drop=True)
        faker = Faker(["en_GB", "zh_CN"])
        faker.seed_instance(seed)
        for p in profiles:
            if p.data_class != DataClass.IDENTIFIER or p.name not in syn.columns:
                continue
            n = p.name.lower()
            if "email" in n or "邮箱" in n:
                syn[p.name] = [f"synthetic-{seed}-{i}@example.invalid" for i in range(len(syn))]
            elif any(k in n for k in ["phone", "mobile", "tel", "手机号", "电话"]):
                syn[p.name] = [f"+00-000-{(seed + i) % 10000:04d}-{i % 10000:04d}" for i in range(len(syn))]
            elif any(k in n for k in ["name", "姓名"]):
                syn[p.name] = [faker.name() for _ in range(len(syn))]
            elif any(k in n for k in ["address", "postcode", "postal", "zip", "地址", "住址", "邮编"]):
                syn[p.name] = [f"Synthetic Address {i + 1}" for i in range(len(syn))]
            else:
                syn[p.name] = [f"SYN-{seed:04d}-{i + 1:06d}" for i in range(len(syn))]
        return syn
