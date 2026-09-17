from __future__ import annotations

import argparse
import json
import sys

from .advisor import hardware_advice, setup_local_ai
from .cli import main as legacy_main
from .deidentify import deidentify_local


_TOP_HELP = """Long Gate — local-first privacy gateway for safe AI data access.

Start here:
  longgate setup                 Detect hardware and configure a verified local model.
  longgate hardware              Inspect local hardware and model-fit recommendations.
  longgate deidentify FILE       Iterative local semantic de-identification + Trust Report.
  longgate run FILE              Structured privacy pipeline.
  longgate doctor                Show installed Long Gate capabilities.

Advanced commands remain available:
  model, inspect, exact, approve-egress, verify-run, sign-run,
  document-inspect, image-inspect, image-ocr-local, pdf-ocr-local,
  audio-inspect, semantic-transform-local, text-inspect, text-redact-local,
  purpose, profiles, row-release-check, setup-prompt

Use `longgate <command> --help` for command-specific options.
"""


def _setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate setup",
        description=(
            "Detect local hardware, recommend a curated GGUF model, and optionally "
            "download + SHA-256 verify it in the Model Vault."
        ),
    )
    parser.add_argument(
        "--ram-gb",
        type=float,
        default=None,
        help="Override automatic RAM detection.",
    )
    parser.add_argument(
        "--vault",
        default=None,
        help="Optional Model Vault directory.",
    )
    parser.add_argument(
        "--recommend-only",
        action="store_true",
        help="Inspect hardware and recommend models without downloading anything.",
    )
    return parser


def _hardware_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate hardware",
        description="Local-only hardware inspection and model-fit advice.",
    )
    parser.add_argument("--ram-gb", type=float, default=None)
    parser.add_argument("--vault", default=None)
    return parser


def _deidentify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate deidentify",
        description=(
            "Run deterministic pre-scrub, local GGUF semantic transformation, "
            "bounded remediation, privacy audit, and an offline Semantic Trust Report."
        ),
    )
    parser.add_argument("input", help="TXT/Markdown/DOCX/PDF with extractable text.")
    parser.add_argument(
        "--model",
        default="auto",
        help="Verified Model Vault alias or local GGUF path. Default: auto.",
    )
    parser.add_argument("--out", required=True, help="Local transformed-text output path.")
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        choices=[1, 2, 3],
        help="Bounded local remediation rounds. Default: 2; maximum: 3.",
    )
    parser.add_argument("--max-tokens", type=int, default=512)
    return parser


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print(_TOP_HELP)
        return

    command = argv[0]
    command_args = argv[1:]

    if command == "hardware":
        args = _hardware_parser().parse_args(command_args)
        _print_json(hardware_advice(ram_gb=args.ram_gb, vault_dir=args.vault))
        return

    if command == "setup":
        args = _setup_parser().parse_args(command_args)
        if args.recommend_only:
            result = hardware_advice(ram_gb=args.ram_gb, vault_dir=args.vault)
        else:
            result = setup_local_ai(ram_gb=args.ram_gb, vault_dir=args.vault)
        _print_json(result)
        return

    if command == "deidentify":
        args = _deidentify_parser().parse_args(command_args)
        result = deidentify_local(
            args.input,
            args.model,
            args.out,
            max_rounds=args.max_rounds,
            max_tokens=args.max_tokens,
        )
        _print_json(result.to_dict())
        return

    legacy_main()


if __name__ == "__main__":
    main()
