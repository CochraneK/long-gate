from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd
from ..types import ColumnProfile


class SyntheticBackend(ABC):
    name: str = "unknown"
    certified_for_egress: bool = False
    description: str = ""

    @abstractmethod
    def generate(self, df: pd.DataFrame, profiles: list[ColumnProfile], seed: int) -> pd.DataFrame:
        raise NotImplementedError
