from __future__ import annotations

from pathlib import Path
from typing import Any

from .aggregate_guard import (
    validate_aggregate_payload,
)
from .executor import (
    correlation,
    describe_numeric,
    group_summary,
    ols,
)
from .inspect import profile_dataframe
from .io import load_table
from .pii import scan_dataframe_values
from .pipeline import RunResult, run_pipeline
from .profiles import get_profile
from .purpose import (
    PurposeDecision,
    route_purpose,
)
from .r_executor import (
    r_describe,
    r_ols,
)


class LongGate:
    """Programmatic API for downstream local-first workflows."""

    def inspect(
        self,
        input_path: str | Path,
    ) -> dict[str, Any]:
        df = load_table(input_path)
        profiles = profile_dataframe(df)
        return {
            "rows": len(df),
            "columns": [
                profile.to_dict()
                for profile in profiles
            ],
            "pii_counts": (
                scan_dataframe_values(
                    df
                ).to_dict()
            ),
        }

    def route(
        self,
        purpose: str,
    ) -> PurposeDecision:
        return route_purpose(purpose)

    def synthesize(
        self,
        input_path: str | Path,
        out_root: str | Path = "./longgate-runs",
        backend: str = "auto",
        seed: int = 42,
        privacy_profile: str = "research",
    ) -> RunResult:
        return run_pipeline(
            input_path,
            out_root,
            backend,
            seed,
            privacy_profile,
        )

    def exact(
        self,
        input_path: str | Path,
        analysis: str,
        privacy_profile: str = "research",
        engine: str = "python",
        **kwargs: Any,
    ) -> dict[str, Any]:
        df = load_table(input_path)
        profiles = profile_dataframe(df)
        policy = get_profile(
            privacy_profile
        )

        if engine not in {
            "python",
            "r",
        }:
            raise ValueError(
                "Exact engine must be 'python' or 'r'."
            )

        if engine == "r":
            if analysis == "describe":
                result = r_describe(
                    df,
                    profiles,
                    min_dataset_size=(
                        policy.min_dataset_size
                    ),
                )
            elif analysis == "ols":
                result = r_ols(
                    df,
                    profiles,
                    kwargs["outcome"],
                    list(
                        kwargs["predictors"]
                    ),
                    min_dataset_size=(
                        policy.min_dataset_size
                    ),
                    min_group_size=(
                        policy.min_group_size
                    ),
                )
            else:
                raise ValueError(
                    "R exact engine currently supports "
                    "'describe' and 'ols' only."
                )
        elif analysis == "describe":
            result = describe_numeric(
                df,
                profiles,
                min_dataset_size=(
                    policy.min_dataset_size
                ),
            )
        elif analysis == "correlation":
            result = correlation(
                df,
                profiles,
                min_dataset_size=(
                    policy.min_dataset_size
                ),
            )
        elif analysis == "group_summary":
            result = group_summary(
                df,
                profiles,
                kwargs["group_by"],
                kwargs["value"],
                min_group_size=(
                    policy.min_group_size
                ),
            )
        elif analysis == "ols":
            result = ols(
                df,
                profiles,
                kwargs["outcome"],
                list(
                    kwargs["predictors"]
                ),
                min_dataset_size=(
                    policy.min_dataset_size
                ),
                min_group_size=(
                    policy.min_group_size
                ),
            )
        else:
            raise ValueError(
                "Unsupported exact analysis: "
                f"{analysis}"
            )

        return validate_aggregate_payload(
            result
        )
