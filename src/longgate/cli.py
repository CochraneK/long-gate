from __future__ import annotations

import argparse
import json

from .aggregate_guard import (
    validate_aggregate_payload,
)
from .doctor import capabilities
from .documents import inspect_document_file
from .executor import (
    correlation,
    describe_numeric,
    group_summary,
    ols,
)
from .inspect import profile_dataframe
from .io import load_table
from .pii import scan_dataframe_values
from .pipeline import run_pipeline
from .profiles import (
    get_profile,
    list_profiles,
)
from .provenance import verify_provenance
from .purpose import route_purpose
from .r_executor import (
    r_describe,
    r_ols,
)
from .unstructured import (
    inspect_text_file,
    redact_text_file_local,
)


def _add_profile_argument(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--profile",
        default="research",
        choices=[
            profile.name
            for profile in list_profiles()
        ],
        help=(
            "Engineering privacy preset; "
            "not a compliance certification."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate",
        description=(
            "Long Gate — local-first privacy "
            "orchestration for safe AI data access."
        ),
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run = sub.add_parser(
        "run",
        help=(
            "Inspect → synthesize → audit "
            "→ gate → report."
        ),
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
            "Row-level egress remains fail-closed."
        ),
    )
    run.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    _add_profile_argument(run)

    sub.add_parser(
        "doctor",
        help=(
            "Show local Long Gate capabilities "
            "and optional engines."
        ),
    )

    sub.add_parser(
        "profiles",
        help=(
            "Show engineering privacy presets "
            "and their thresholds."
        ),
    )

    inspect_cmd = sub.add_parser(
        "inspect",
        help=(
            "Local schema and PII-count "
            "inspection only."
        ),
    )
    inspect_cmd.add_argument(
        "input"
    )

    purpose_cmd = sub.add_parser(
        "purpose",
        help=(
            "Show the disclosure mode "
            "for a requested purpose."
        ),
    )
    purpose_cmd.add_argument(
        "name"
    )

    exact = sub.add_parser(
        "exact",
        help="Run safe exact statistics locally.",
    )
    exact.add_argument(
        "input"
    )
    exact.add_argument(
        "analysis",
        choices=[
            "describe",
            "correlation",
            "group-summary",
            "ols",
        ],
    )
    exact.add_argument(
        "--group-by"
    )
    exact.add_argument(
        "--value"
    )
    exact.add_argument(
        "--outcome"
    )
    exact.add_argument(
        "--predictor",
        action="append",
        default=[],
    )
    exact.add_argument(
        "--engine",
        choices=[
            "python",
            "r",
        ],
        default="python",
        help=(
            "Exact computation engine. "
            "R uses fixed Long Gate templates only."
        ),
    )
    _add_profile_argument(exact)

    verify = sub.add_parser(
        "verify-run",
        help=(
            "Verify SHA-256 provenance "
            "for a completed run directory."
        ),
    )
    verify.add_argument(
        "run_dir"
    )

    document_inspect = sub.add_parser(
        "document-inspect",
        help=(
            "Extract and inspect TXT/MD/DOCX/PDF locally. "
            "The result never grants network egress."
        ),
    )
    document_inspect.add_argument(
        "input"
    )

    text_inspect = sub.add_parser(
        "text-inspect",
        help=(
            "Inspect TXT/Markdown locally; "
            "free text remains network-blocked."
        ),
    )
    text_inspect.add_argument(
        "input"
    )

    text_redact = sub.add_parser(
        "text-redact-local",
        help=(
            "Create a local preview redaction. "
            "The output is not granted "
            "network-egress permission."
        ),
    )
    text_redact.add_argument(
        "input"
    )
    text_redact.add_argument(
        "--out",
        required=True,
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "doctor":
        print(
            json.dumps(
                [
                    capability.to_dict()
                    for capability in capabilities()
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "profiles":
        print(
            json.dumps(
                [
                    profile.to_dict()
                    for profile in list_profiles()
                ],
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
            args.profile,
        )
        print(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "status": result.status,
                    "output": str(
                        result.out_dir
                    ),
                    "report": str(
                        result.report_path
                    ),
                    "synthetic": str(
                        result.synthetic_path
                    ),
                    "provenance": str(
                        result.provenance_path
                    ),
                    "safe_payload": (
                        str(
                            result.staged_payload
                        )
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
        df = load_table(
            args.input
        )
        profiles = profile_dataframe(
            df
        )
        pii = scan_dataframe_values(
            df
        )
        print(
            json.dumps(
                {
                    "rows": len(df),
                    "columns": [
                        profile.to_dict()
                        for profile in profiles
                    ],
                    "pii_counts": pii.to_dict(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "purpose":
        decision = route_purpose(
            args.name
        )
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

    if args.command == "verify-run":
        print(
            json.dumps(
                verify_provenance(
                    args.run_dir
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "document-inspect":
        result = inspect_document_file(
            args.input
        )
        print(
            json.dumps(
                result.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "text-inspect":
        result = inspect_text_file(
            args.input
        )
        print(
            json.dumps(
                result.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "text-redact-local":
        output = redact_text_file_local(
            args.input,
            args.out,
        )
        print(
            json.dumps(
                {
                    "output": str(output),
                    "release_allowed": False,
                    "note": (
                        "Local preview redaction only; "
                        "not a semantic privacy guarantee."
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "exact":
        df = load_table(
            args.input
        )
        profiles = profile_dataframe(
            df
        )
        policy = get_profile(
            args.profile
        )

        if args.engine == "r":
            if args.analysis == "describe":
                result = r_describe(
                    df,
                    profiles,
                    min_dataset_size=(
                        policy.min_dataset_size
                    ),
                )
            elif args.analysis == "ols":
                if (
                    not args.outcome
                    or not args.predictor
                ):
                    raise SystemExit(
                        "--outcome and at least one "
                        "--predictor are required"
                    )
                result = r_ols(
                    df,
                    profiles,
                    args.outcome,
                    args.predictor,
                    min_dataset_size=(
                        policy.min_dataset_size
                    ),
                    min_group_size=(
                        policy.min_group_size
                    ),
                )
            else:
                raise SystemExit(
                    "R engine currently supports "
                    "describe and ols only."
                )
        elif args.analysis == "describe":
            result = describe_numeric(
                df,
                profiles,
                min_dataset_size=(
                    policy.min_dataset_size
                ),
            )
        elif args.analysis == "correlation":
            result = correlation(
                df,
                profiles,
                min_dataset_size=(
                    policy.min_dataset_size
                ),
            )
        elif args.analysis == "group-summary":
            if (
                not args.group_by
                or not args.value
            ):
                raise SystemExit(
                    "--group-by and --value are required"
                )
            result = group_summary(
                df,
                profiles,
                args.group_by,
                args.value,
                min_group_size=(
                    policy.min_group_size
                ),
            )
        else:
            if (
                not args.outcome
                or not args.predictor
            ):
                raise SystemExit(
                    "--outcome and at least one "
                    "--predictor are required"
                )
            result = ols(
                df,
                profiles,
                args.outcome,
                args.predictor,
                min_dataset_size=(
                    policy.min_dataset_size
                ),
                min_group_size=(
                    policy.min_group_size
                ),
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
