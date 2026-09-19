from __future__ import annotations

import json
import shutil
# Gitleaks is an explicit local executable resolved with shutil.which. Calls use
# an argv list with shell=False; the subprocess boundary is intentional.
import subprocess  # nosec B404
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class SecretScanResult:
    engine: str
    engine_available: bool
    mode: str
    findings: int
    files: list[str]
    rules: dict[str, int]
    release_allowed: bool
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_relative(raw: object, root: Path) -> str:
    if not isinstance(raw, str) or not raw:
        return "<unknown>"
    path = Path(raw)
    try:
        if path.is_absolute():
            return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError):
        return path.name or "<external>"
    return raw.replace("\\", "/")


def scan_secrets_with_gitleaks(
    path: str | Path,
    *,
    history: bool = False,
) -> SecretScanResult:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(target)

    executable = shutil.which("gitleaks")
    if executable is None:
        return SecretScanResult(
            engine="gitleaks",
            engine_available=False,
            mode="git-history" if history else "directory",
            findings=0,
            files=[],
            rules={},
            release_allowed=False,
            note=(
                "Gitleaks is not installed. Install the local gitleaks binary and rerun. "
                "Long Gate does not upload source files to a remote secret scanner."
            ),
        )

    with tempfile.TemporaryDirectory(prefix="longgate-secret-scan-") as tmp:
        report = Path(tmp) / "gitleaks.json"
        command = [
            executable,
            "git" if history else "dir",
            str(target),
            "--report-format",
            "json",
            "--report-path",
            str(report),
            "--exit-code",
            "0",
            "--no-banner",
            "--redact=100",
        ]
        # The executable is resolved locally, arguments are not passed through a shell,
        # and user-controlled target data is one argv element rather than command text.
        completed = subprocess.run(  # nosec B603
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=300,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Gitleaks scan failed without producing a trusted result. "
                f"exit_code={completed.returncode}"
            )

        if not report.exists():
            findings_raw: object = []
        else:
            findings_raw = json.loads(report.read_text(encoding="utf-8"))

    if not isinstance(findings_raw, list):
        raise ValueError("Unexpected gitleaks JSON report format.")

    files: set[str] = set()
    rules: dict[str, int] = {}
    for item in findings_raw:
        if not isinstance(item, dict):
            continue
        files.add(_safe_relative(item.get("File"), target))
        rule = item.get("RuleID")
        rule_name = str(rule) if rule else "unknown"
        rules[rule_name] = rules.get(rule_name, 0) + 1

    return SecretScanResult(
        engine="gitleaks",
        engine_available=True,
        mode="git-history" if history else "directory",
        findings=len(findings_raw),
        files=sorted(files),
        rules=dict(sorted(rules.items())),
        release_allowed=False,
        note=(
            "Secret values and matched text are intentionally omitted. "
            "The scan runs locally and its result is not an egress authorization."
        ),
    )
