from __future__ import annotations

import argparse
import json
import sys

from .advisor import hardware_advice, setup_local_ai
from .cli import main as legacy_main
from .deidentify import deidentify_local
from .doctor import capabilities, deep_local_llm_check
from .document_deidentify import deidentify_file_copy


_TOP_HELP = """Long Gate — local-first privacy gateway for safe AI data access.

Start here:
  longgate setup                 Detect hardware and configure a verified local model.
  longgate hardware              Inspect local hardware and model-fit recommendations.
  longgate deidentify FILE       Create a format-preserving TXT/Markdown/HTML/XLSX/DOCX copy.
  longgate semantic-summarize FILE
                                 Create a strongly abstracted local semantic summary.
  longgate run FILE              Structured privacy pipeline.
  longgate doctor                Show installed Long Gate capabilities.

Advanced commands remain available:
  model, inspect, exact, approve-egress, verify-run, sign-run,
  document-inspect, image-inspect, image-ocr-local, pdf-ocr-local,
  audio-inspect, semantic-transform-local, text-inspect, text-redact-local,
  purpose, profiles, row-release-check, setup-prompt

Use longgate <command> --help for command-specific options.
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


def _doctor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate doctor",
        description=(
            "Run real local import checks. Add --deep to verify the resolved GGUF "
            "model file and perform one tiny non-sensitive local inference."
        ),
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Also resolve the model and perform a minimal local inference.",
    )
    parser.add_argument(
        "--model",
        default="auto",
        help="Verified Model Vault alias or local GGUF path for --deep. Default: auto.",
    )
    return parser


def _deidentify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate deidentify",
        description=(
            "Create a same-format TXT/Markdown/HTML/XLSX/DOCX de-identified copy by replacing "
            "explicit direct identifiers locally. The source file is never overwritten."
        ),
    )
    parser.add_argument("input", help="TXT, Markdown, HTML, XLSX, or DOCX input file.")
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Output path. Default: <input>.deidentified with the original extension. "
            "The output must keep the same extension."
        ),
    )
    return parser


def _semantic_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgate semantic-summarize",
        description=(
            "Run deterministic pre-scrub, local GGUF identity-detached abstraction, "
            "bounded remediation, privacy audit, and an offline Semantic Trust Report."
        ),
    )
    parser.add_argument("input", help="TXT/Markdown/HTML/DOCX/PDF with extractable text.")
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
    parser.add_argument(
        "--chunking",
        choices=["none", "safe"],
        default="none",
        help="Use explicit paragraph-aware chunks for long documents. Default: none.",
    )
    parser.add_argument("--chunk-size", type=int, default=3000)
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

    if command == "doctor":
        args = _doctor_parser().parse_args(command_args)
        result = [capability.to_dict() for capability in capabilities()]
        if args.deep:
            result.append(deep_local_llm_check(args.model).to_dict())
        _print_json(result)
        return

    if command == "deidentify":
        args = _deidentify_parser().parse_args(command_args)
        result = deidentify_file_copy(args.input, args.out)
        _print_json(result.to_dict())
        return

    if command == "semantic-summarize":
        args = _semantic_parser().parse_args(command_args)
        result = deidentify_local(
            args.input,
            args.model,
            args.out,
            max_rounds=args.max_rounds,
            max_tokens=args.max_tokens,
            chunking=args.chunking,
            chunk_size=args.chunk_size,
        )
        _print_json(result.to_dict())
        return

    legacy_main()


if __name__ == "__main__":
    main()
