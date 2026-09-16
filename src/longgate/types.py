from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class DataClass(str, Enum):
    IDENTIFIER = "identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    SENSITIVE = "sensitive"
    GENERAL = "general"
    FREE_TEXT = "free_text"


class ReleaseClass(str, Enum):
    RAW = "raw"
    PSEUDONYMIZED = "pseudonymized"
    SYNTHETIC = "synthetic"
    AGGREGATE = "aggregate"


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    data_class: DataClass
    strategy: str
    non_null: int
    unique: int
    unique_ratio: float
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["data_class"] = self.data_class.value
        return d


@dataclass
class AuditResult:
    passed: bool
    backend_certified: bool
    exact_row_overlap: int
    identifier_overlap: int
    quasi_combo_overlap: int
    rare_quasi_overlap: int
    near_copy_rate: float | None
    free_text_columns: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
