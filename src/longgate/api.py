from __future__ import annotations

from pathlib import Path
from typing import Any

from .aggregate_guard import validate_aggregate_payload
from .executor import correlation, describe_numeric, group_summary, ols
from .inspect import profile_dataframe
from .io import load_table
from .pii import scan_dataframe_values
from .pipeline import RunResult, run_pipeline
from .purpose import PurposeDecision, route_purpose


class LongGate:
    """Programmatic API for downstream projects such as research agents."""

    def inspect(self, input_path: str | Path) -> dict[str, Any]:
        df = load_table(input_path)
        profiles = profile_dataframe(df)
        return {
            "rows": len(df),
            "columns": [p.to_dict() for p in profiles],
            "pii_counts": scan_dataframe_values(df).to_dict(),
        }

    def route(self, purpose: str) -> PurposeDecision:
        return route_purpose(purpose)

    def synthesize(
        self,
        input_path: str | Path,
        out_root: str | Path = "./longgate-runs",
        backend: str = "auto",
        seed: int = 42,
    ) -> RunResult:
        return run_pipeline(input_path, out_root, backend, seed)

    def exact(
        self,
        input_path: str | Path,
        analysis: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        df = load_table(input_path)
        profiles = profile_dataframe(df)

        if analysis == "describe":
            result = describe_numeric(df, profiles)
        elif analysis == "correlation":
            result = correlation(df, profiles)
        elif analysis == "group_summary":
            result = group_summary(
                df,
                profiles,
                kwargs["group_by"],
                kwargs["value"],
            )
        elif analysis == "ols":
            result = ols(
                df,
                profiles,
                kwargs["outcome"],
                list(kwargs["predictors"]),
            )
        else:
            raise ValueError(f"Unsupported exact analysis: {analysis}")

        return validate_aggregate_payload(result)
