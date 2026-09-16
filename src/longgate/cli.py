from __future__ import annotations

import argparse
import json

from .aggregate_guard import validate_aggregate_payload
from .doctor import capabilities
from .executor import correlation, describe_numeric, group_summary, ols
from .inspect import profile_dataframe
from .io import load_table
from .pii import scan_dataframe_values
from .pipeline import run_pipeline
from .purpose import route_purpose


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="longgate",
        description="Long Gate — local-first privacy orchestration for safe AI data access.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="Inspect → synthesize → audit → gate → report.",
    )
    run.add_argument(
        "input",
        help="CSV, XLSX, JSON, or Parquet file",
    )
    run.add_argument(
        "--out",
        default="./longgate-runs",
    )
    run.add_argument(
        "--backend",
        default="auto",
        help=(
            "auto, demo, synthcity[:plugin], or mostlyai. "
            "v0.2 row-level egress remains fail-closed."
        ),
    )
    run.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    sub.add_parser(
        "doctor",
        help="Show local Long Gate capabilities and optional engines.",
    )

    inspect_cmd = sub.add_parser(
        "inspect",
        help="Local schema and PII-count inspection only.",
    )
    inspect_cmd.add_argument("input")

    purpose_cmd = sub.add_parser(
        "purpose",
        help="Show the disclosure mode for a requested purpose.",
    )
    purpose_cmd.add_argument("name")

    exact = sub.add_parser(
        "exact",
        help="Run safe exact statistics locally.",
    )
    exact.add_argument("input")
    exact.add_argument(
        "analysis",
        choices=[
            "describe",
            "correlation",
            "group-summary",
            "ols",
        ],
    )
    exact.add_argument("--group-by")
    exact.add_argument("--value")
    exact.add_argument("--outcome")
    exact.add_argument(
        "--predictor",
        action="append",
        default=[],
    )

    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "doctor":
        print(
            json.dumps(
                [c.to_dict() for c in capabilities()],
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "run":
        result = run_pipeline(
            args.input,
            args.out,
            args.backend,
            args.seed,
        )
        print(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "status": result.status,
                    "output": str(result.out_dir),
                    "report": str(result.report_path),
                    "synthetic": str(result.synthetic_path),
                    "safe_payload": (
                        str(result.staged_payload)
                        if result.staged_payload
                        else None
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "inspect":
        df = load_table(args.input)
        profiles = profile_dataframe(df)
        pii = scan_dataframe_values(df)
        print(
            json.dumps(
                {
                    "rows": len(df),
                    "columns": [
                        p.to_dict()
                        for p in profiles
                    ],
                    "pii_counts": pii.to_dict(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "purpose":
        decision = route_purpose(args.name)
        print(
            json.dumps(
                {
                    "purpose": decision.purpose,
                    "mode": decision.mode.value,
                    "reason": decision.reason,
                },
                indent=2,
            )
        )
        return

    if args.command == "exact":
        df = load_table(args.input)
        profiles = profile_dataframe(df)

        if args.analysis == "describe":
            result = describe_numeric(
                df,
                profiles,
            )
        elif args.analysis == "correlation":
            result = correlation(
                df,
                profiles,
            )
        elif args.analysis == "group-summary":
            if not args.group_by or not args.value:
                raise SystemExit(
                    "--group-by and --value are required"
                )
            result = group_summary(
                df,
                profiles,
                args.group_by,
                args.value,
            )
        else:
            if not args.outcome or not args.predictor:
                raise SystemExit(
                    "--outcome and at least one --predictor are required"
                )
            result = ols(
                df,
                profiles,
                args.outcome,
                args.predictor,
            )

        result = validate_aggregate_payload(
            result
        )
        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
