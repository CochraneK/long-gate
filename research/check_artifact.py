from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from research.run_experiments import validate_config
from research.semantic_redteam import load_cases

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "research" / "README.md",
    ROOT / "research" / "research-questions.md",
    ROOT / "research" / "protocol.md",
    ROOT / "research" / "experiment-matrix.md",
    ROOT / "research" / "ARTIFACT_FREEZE.md",
    ROOT / "research" / "datasets" / "README.md",
    ROOT / "research" / "results" / "README.md",
    ROOT / "research" / "configs" / "paper-smoke.json",
    ROOT / "research" / "redteam" / "semantic_synthetic_v1.jsonl",
]


def _tracked_result_files() -> list[str]:
    try:
        result = subprocess.run(  # noqa: S603 - fixed local git command, no user shell
            ["git", "ls-files", "research/results"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required research artifact file: {path.relative_to(ROOT)}")

    config_dir = ROOT / "research" / "configs"
    for path in sorted(config_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            validate_config(payload)
        except Exception as exc:
            errors.append(f"invalid research config {path.relative_to(ROOT)}: {exc}")

    corpus = ROOT / "research" / "redteam" / "semantic_synthetic_v1.jsonl"
    if corpus.is_file():
        try:
            cases = load_cases(corpus)
            if len(cases) < 5:
                errors.append("synthetic semantic red-team corpus must contain at least 5 cases")
        except Exception as exc:
            errors.append(f"invalid semantic red-team corpus: {exc}")

    tracked_results = _tracked_result_files()
    unexpected = [path for path in tracked_results if path != "research/results/README.md"]
    if unexpected:
        errors.append(
            "generated development results are tracked unexpectedly: " + ", ".join(unexpected)
        )

    smoke = config_dir / "paper-smoke.json"
    if smoke.is_file():
        payload = json.loads(smoke.read_text(encoding="utf-8"))
        purpose = str(payload.get("purpose", "")).lower()
        if "not paper evidence" not in purpose:
            errors.append("paper-smoke config must explicitly state that it is not paper evidence")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Long Gate research-artifact structure.")
    parser.parse_args()
    errors = check()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Research artifact structure OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
