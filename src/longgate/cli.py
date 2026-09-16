from __future__ import annotations

import argparse
import json
from pathlib import Path

from .aggregate_guard import (
    validate_aggregate_payload,
)
from .approval import issue_approval
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
from .model_vault import catalog as model_catalog
from .model_vault import (
    install_model,
    list_installed,
    recommend_model,
    setup_model,
    verify_model,
)
from .onboarding import AI_SETUP_PROMPT
from .pii import scan_dataframe_values
from .pipeline import run_pipeline
from .profiles import (
    list_profiles,
    resolve_profile,
)
from .provenance import sign_provenance, verify_provenance
from .purpose import route_purpose
from .r_executor import (
    r_describe,
    r_ols,
)
from .semantic import semantic_transform_local
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
    parser.add_argument(
        "--profile-file",
        default=None,
        help=(
            "Optional reviewed organization JSON profile. "
            "Overrides --profile; pre-1.0 custom profiles cannot enable "
            "row-level synthetic egress."
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

    sub.add_parser(
        "setup-prompt",
        help=(
            "Print a copyable prompt that tells another AI "
            "how to configure Long Gate safely."
        ),
    )

    model = sub.add_parser(
        "model",
        help=(
            "Recommend, install, verify, and inspect local GGUF models."
        ),
    )
    model_sub = model.add_subparsers(
        dest="model_command",
        required=True,
    )

    setup = model_sub.add_parser(
        "setup",
        help=(
            "Automatically recommend, download, verify, "
            "and set the default local model."
        ),
    )
    setup.add_argument(
        "--ram-gb",
        type=float,
        default=None,
        help=(
            "Override automatic system-RAM detection."
        ),
    )
    setup.add_argument(
        "--vault",
        default=None,
        help="Optional Model Vault directory.",
    )

    recommend = model_sub.add_parser(
        "recommend",
        help=(
            "Recommend a curated local model for this machine."
        ),
    )
    recommend.add_argument(
        "--ram-gb",
        type=float,
        default=None,
        help=(
            "Override automatic system-RAM detection."
        ),
    )

    model_sub.add_parser(
        "catalog",
        help="Show the curated Long Gate model catalog.",
    )

    install = model_sub.add_parser(
        "install",
        help=(
            "Download and SHA-256 verify a model in network-enabled setup mode."
        ),
    )
    install.add_argument(
        "alias"
    )
    install.add_argument(
        "--vault",
        default=None,
        help="Optional Model Vault directory.",
    )

    model_list = model_sub.add_parser(
        "list",
        help="List models registered in the local Model Vault.",
    )
    model_list.add_argument(
        "--vault",
        default=None,
    )

    verify_model_cmd = model_sub.add_parser(
        "verify",
        help="Recompute and verify a Model Vault SHA-256.",
    )
    verify_model_cmd.add_argument(
        "alias"
    )
    verify_model_cmd.add_argument(
        "--vault",
        default=None,
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

    approve = sub.add_parser(
        "approve-egress",
        help=(
            "Locally approve one egress artifact for a declared purpose, "
            "binding approval to its SHA-256."
        ),
    )
    approve.add_argument("artifact")
    approve.add_argument(
        "--workspace",
        required=True,
        help="Approved egress workspace root.",
    )
    approve.add_argument(
        "--ledger",
        required=True,
        help="Append-only local approval ledger path.",
    )
    approve.add_argument(
        "--purpose",
        required=True,
        help="Exact purpose string the network consumer must declare.",
    )

    sign = sub.add_parser(
        "sign-run",
        help=(
            "Sign an already-valid run provenance with an existing "
            "Ed25519 signing key."
        ),
    )
    sign.add_argument("run_dir")
    sign.add_argument(
        "--signing-key",
        required=True,
        help=(
            "Path to an existing PEM Ed25519 signing key. "
            "Long Gate does not generate or copy key material."
        ),
    )

    verify = sub.add_parser(
        "verify-run",
        help=(
            "Verify SHA-256 provenance and optionally an Ed25519 signature."
        ),
    )
    verify.add_argument("run_dir")
    verify.add_argument(
        "--public-key",
        default=None,
        help=(
            "Optional PEM Ed25519 public key. When supplied, "
            "a valid signature is required."
        ),
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

    semantic_preview = sub.add_parser(
        "semantic-transform-local",
        help=(
            "Run an in-process local GGUF privacy transformation. "
            "The output remains network-blocked."
        ),
    )
    semantic_preview.add_argument(
        "input"
    )
    semantic_preview.add_argument(
        "--model",
        required=True,
    )
    semantic_preview.add_argument(
        "--out",
        required=True,
    )
    semantic_preview.add_argument(
        "--max-tokens",
        type=int,
        default=512,
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

    if args.command == "setup-prompt":
        print(
            AI_SETUP_PROMPT
        )
        return

    if args.command == "model":
        if args.model_command == "setup":
            result = setup_model(
                args.ram_gb,
                args.vault,
            )
        elif args.model_command == "recommend":
            result = recommend_model(
                args.ram_gb
            )
        elif args.model_command == "catalog":
            result = model_catalog()
        elif args.model_command == "install":
            result = install_model(
                args.alias,
                args.vault,
            )
        elif args.model_command == "list":
            result = list_installed(
                args.vault
            )
        else:
            result = verify_model(
                args.alias,
                args.vault,
            )
        print(
            json.dumps(
                result,
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
            args.profile_file,
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
                    "release_class": result.release_class,
                    "next_actions": result.next_actions,
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

    if args.command == "approve-egress":
        workspace = Path(args.workspace).expanduser().resolve()
        artifact = Path(args.artifact).expanduser().resolve()
        try:
            relative = artifact.relative_to(workspace)
        except ValueError as exc:
            raise SystemExit(
                "Artifact must be inside --workspace."
            ) from exc
        record = issue_approval(
            workspace,
            relative,
            args.ledger,
            args.purpose,
        )
        print(
            json.dumps(
                record.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "sign-run":
        signature_path = sign_provenance(
            args.run_dir,
            args.signing_key,
        )
        print(
            json.dumps(
                {
                    "signature": str(signature_path),
                    "note": (
                        "Keep signing keys outside Long Gate run directories; "
                        "trust/distribute the public key independently."
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "verify-run":
        print(
            json.dumps(
                verify_provenance(
                    args.run_dir,
                    args.public_key,
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

    if args.command == "semantic-transform-local":
        result = semantic_transform_local(
            args.input,
            args.model,
            args.out,
            max_tokens=args.max_tokens,
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
        policy = resolve_profile(
            args.profile,
            args.profile_file,
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
