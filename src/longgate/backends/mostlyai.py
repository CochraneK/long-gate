from __future__ import annotations

import pandas as pd
from faker import Faker

from .base import SyntheticBackend
from ..types import ColumnProfile, DataClass


class MostlyAIBackend(SyntheticBackend):
    """MOSTLY AI local-mode adapter. v0.2 remains fail-closed for row-level egress."""

    name = "mostlyai"
    certified_for_egress = False
    description = "MOSTLY AI local-mode synthesis preview; identifiers are excluded before training."

    def generate(self, df: pd.DataFrame, profiles: list[ColumnProfile], seed: int) -> pd.DataFrame:
        try:
            from mostlyai.sdk import MostlyAI
        except ImportError as exc:
            raise RuntimeError(
                "MOSTLY AI backend requested but not installed. Run: pip install 'long-gate[mostlyai]'"
            ) from exc

        identifier_cols = [
            p.name for p in profiles
            if p.data_class == DataClass.IDENTIFIER and p.name in df.columns
        ]
        model_df = df.drop(columns=identifier_cols, errors="ignore").copy()
        mostly = MostlyAI(local=True)
        generator = mostly.train(data=model_df, start=True, wait=True)
        synthetic_dataset = mostly.generate(generator, size=len(df))
        syn = synthetic_dataset.data()
        syn = syn.reset_index(drop=True)

        for col in identifier_cols:
            syn[col] = None
        syn = syn.reindex(columns=df.columns)

        fake = Faker(["en_GB", "zh_CN"])
        fake.seed_instance(seed)
        for p in profiles:
            if p.data_class != DataClass.IDENTIFIER or p.name not in syn.columns:
                continue
            n = p.name.lower()
            if "email" in n or "邮箱" in n:
                syn[p.name] = [f"synthetic-{seed}-{i}@example.invalid" for i in range(len(syn))]
            elif any(k in n for k in ["phone", "mobile", "tel", "手机号", "电话"]):
                syn[p.name] = [f"+00-000-{(seed+i)%10000:04d}-{i%10000:04d}" for i in range(len(syn))]
            elif any(k in n for k in ["name", "姓名"]):
                syn[p.name] = [fake.name() for _ in range(len(syn))]
            elif any(k in n for k in ["address", "postcode", "postal", "zip", "地址", "住址", "邮编"]):
                syn[p.name] = [f"Synthetic Address {i+1}" for i in range(len(syn))]
            else:
                syn[p.name] = [f"SYN-{seed:04d}-{i+1:06d}" for i in range(len(syn))]
        return syn
