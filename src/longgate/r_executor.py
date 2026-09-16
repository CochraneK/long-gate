from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from .types import ColumnProfile, DataClass


class RUnavailable(RuntimeError):
    pass


_FIXED_R_SCRIPT = r"""
args <- commandArgs(trailingOnly = TRUE)
mode <- args[[1]]
input_path <- args[[2]]
output_path <- args[[3]]
meta_path <- args[[4]]

data <- read.csv(
    input_path,
    check.names = FALSE,
    stringsAsFactors = TRUE
)

if (mode == "describe") {
    rows <- list()
    for (name in names(data)) {
        x <- data[[name]]
        if (!is.numeric(x)) {
            next
        }
        clean <- x[!is.na(x)]
        if (length(clean) == 0) {
            rows[[length(rows) + 1]] <- data.frame(
                term = name,
                n = 0,
                mean = NA,
                sd = NA,
                min = NA,
                max = NA
            )
        } else {
            rows[[length(rows) + 1]] <- data.frame(
                term = name,
                n = length(clean),
                mean = mean(clean),
                sd = if (length(clean) > 1) sd(clean) else NA,
                min = min(clean),
                max = max(clean)
            )
        }
    }
    if (length(rows) == 0) {
        result <- data.frame(
            term = character(),
            n = integer(),
            mean = numeric(),
            sd = numeric(),
            min = numeric(),
            max = numeric()
        )
    } else {
        result <- do.call(rbind, rows)
    }
    write.csv(
        result,
        output_path,
        row.names = FALSE
    )
    write.csv(
        data.frame(n_rows = nrow(data)),
        meta_path,
        row.names = FALSE
    )
} else if (mode == "ols") {
    fit <- lm(
        y ~ .,
        data = data,
        na.action = na.omit
    )
    summary_fit <- summary(fit)
    coefficients <- summary_fit$coefficients
    result <- data.frame(
        term = rownames(coefficients),
        coef = coefficients[, 1],
        se = coefficients[, 2],
        statistic = coefficients[, 3],
        p = coefficients[, 4]
    )
    write.csv(
        result,
        output_path,
        row.names = FALSE
    )
    write.csv(
        data.frame(
            nobs = nobs(fit),
            r_squared = summary_fit$r.squared,
            adj_r_squared = summary_fit$adj.r.squared
        ),
        meta_path,
        row.names = FALSE
    )
} else {
    stop("Unsupported fixed Long Gate R mode.")
}
"""


def _rscript_path() -> str:
    path = shutil.which("Rscript")
    if not path:
        raise RUnavailable(
            "Rscript was not found. Install R locally and ensure "
            "Rscript is on PATH."
        )
    return path


def _identifier_columns(
    profiles: list[ColumnProfile],
) -> set[str]:
    return {
        profile.name
        for profile in profiles
        if profile.data_class == DataClass.IDENTIFIER
    }


def _safe_numeric_columns(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
) -> list[str]:
    identifiers = _identifier_columns(profiles)
    return [
        column
        for column in df.columns
        if (
            column not in identifiers
            and pd.api.types.is_numeric_dtype(df[column])
        )
    ]


def _run_fixed_r(
    frame: pd.DataFrame,
    mode: str,
    timeout: int = 60,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rscript = _rscript_path()
    with tempfile.TemporaryDirectory(
        prefix="longgate-r-"
    ) as temp_dir:
        root = Path(temp_dir)
        input_path = root / "input.csv"
        output_path = root / "result.csv"
        meta_path = root / "meta.csv"
        script_path = root / "analysis.R"

        frame.to_csv(
            input_path,
            index=False,
        )
        script_path.write_text(
            _FIXED_R_SCRIPT,
            encoding="utf-8",
        )

        command = [
            rscript,
            str(script_path),
            mode,
            str(input_path),
            str(output_path),
            str(meta_path),
        ]
        subprocess.run(  # nosec B603
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return (
            pd.read_csv(output_path),
            pd.read_csv(meta_path),
        )


def r_describe(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    min_dataset_size: int = 10,
) -> dict[str, Any]:
    if len(df) < min_dataset_size:
        raise ValueError(
            "Dataset is too small for released descriptive statistics."
        )

    columns = _safe_numeric_columns(
        df,
        profiles,
    )
    aliases = {
        f"x{index}": column
        for index, column in enumerate(columns)
    }
    frame = df[columns].rename(
        columns={
            original: alias
            for alias, original in aliases.items()
        }
    )
    result, meta = _run_fixed_r(
        frame,
        "describe",
    )

    output: dict[str, Any] = {
        "engine": "R",
        "analysis": "describe",
        "n_rows": int(
            meta.iloc[0]["n_rows"]
        ),
        "columns": {},
    }
    for row in result.to_dict(
        orient="records"
    ):
        original = aliases[str(row["term"])]
        output["columns"][original] = {
            "n": int(row["n"]),
            "mean": (
                None
                if pd.isna(row["mean"])
                else float(row["mean"])
            ),
            "std": (
                None
                if pd.isna(row["sd"])
                else float(row["sd"])
            ),
            "min": (
                None
                if pd.isna(row["min"])
                else float(row["min"])
            ),
            "max": (
                None
                if pd.isna(row["max"])
                else float(row["max"])
            ),
        }
    return output


def _friendly_r_term(
    term: str,
    aliases: dict[str, str],
) -> str:
    if term == "(Intercept)":
        return "const"

    for alias in sorted(
        aliases,
        key=len,
        reverse=True,
    ):
        if term == alias:
            return aliases[alias]
        if term.startswith(alias):
            level = term[len(alias) :]
            return (
                f"{aliases[alias]}[{level}]"
            )
    return term


def r_ols(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    outcome: str,
    predictors: list[str],
    min_dataset_size: int = 10,
    min_group_size: int = 5,
) -> dict[str, Any]:
    identifiers = _identifier_columns(profiles)
    selected = [
        outcome,
        *predictors,
    ]

    if any(
        column in identifiers
        for column in selected
    ):
        raise ValueError(
            "Identifier columns cannot be used "
            "in released regression models."
        )
    if (
        outcome not in df.columns
        or any(
            column not in df.columns
            for column in predictors
        )
    ):
        raise KeyError(
            "Unknown regression column."
        )
    if not pd.api.types.is_numeric_dtype(
        df[outcome]
    ):
        raise TypeError(
            "R OLS outcome must be numeric."
        )
    if len(df) < min_dataset_size:
        raise ValueError(
            "Dataset is too small for safe released R OLS."
        )

    aliases = {
        f"x{index}": column
        for index, column in enumerate(predictors)
    }

    frame = pd.DataFrame(
        {
            "y": df[outcome],
        }
    )
    for alias, column in aliases.items():
        series = df[column]
        if not pd.api.types.is_numeric_dtype(
            series
        ):
            counts = (
                series.astype("string")
                .value_counts(dropna=False)
            )
            if (
                len(counts) > 50
                or (
                    counts
                    < min_group_size
                ).any()
            ):
                raise ValueError(
                    f"Categorical predictor {column!r} "
                    "has rare/high-cardinality levels."
                )
        frame[alias] = series

    complete_rows = frame.dropna()
    if len(complete_rows) < max(
        min_dataset_size,
        len(predictors) + 3,
    ):
        raise ValueError(
            "Too few complete observations "
            "for safe released R OLS summary."
        )

    result, meta = _run_fixed_r(
        frame,
        "ols",
    )
    terms: dict[str, dict[str, float]] = {}
    for row in result.to_dict(
        orient="records"
    ):
        friendly = _friendly_r_term(
            str(row["term"]),
            aliases,
        )
        terms[friendly] = {
            "coef": float(row["coef"]),
            "se": float(row["se"]),
            "statistic": float(
                row["statistic"]
            ),
            "p": float(row["p"]),
        }

    meta_row = meta.iloc[0]
    return {
        "engine": "R",
        "model": "OLS",
        "outcome": outcome,
        "predictors": predictors,
        "nobs": int(
            meta_row["nobs"]
        ),
        "r_squared": float(
            meta_row["r_squared"]
        ),
        "adj_r_squared": float(
            meta_row["adj_r_squared"]
        ),
        "terms": terms,
        "execution": (
            "fixed Long Gate R template; "
            "no user-supplied R code executed"
        ),
    }
