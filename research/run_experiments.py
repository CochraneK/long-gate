from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmarks.generate_adversarial import build_dataset
from longgate import __version__
from longgate.audit import audit_dataset
from longgate.backends.demo import DemoBackend
from longgate.inspect import profile_dataframe

ROOT = Path(__file__).resolve().parents[1]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str | None:
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha and len(env_sha) == 40:
        return env_sha
    try:
        result = subprocess.run(  # noqa: S603 - fixed local git command, no user-controlled shell
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and len(value) == 40 else None


def _detect_ram_gb() -> float | None:
    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.ullTotalPhys / (1024**3), 2)
        except (AttributeError, OSError):
            return None

    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return round((page_size * pages) / (1024**3), 2)
    except (AttributeError, OSError, ValueError):
        return None


def environment_snapshot() -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "system_ram_gb": _detect_ram_gb(),
        "long_gate_version": __version__,
        "long_gate_commit": _git_commit(),
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != 1:
        raise ValueError("research config schema_version must be 1")
    suite = config.get("suite")
    if not isinstance(suite, str) or not suite.strip():
        raise ValueError("research config requires non-empty suite")
    seeds = config.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("research config requires at least one seed")
    if not all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds):
        raise ValueError("research config seeds must be integers")
    experiments = config.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        raise ValueError("research config requires experiments")
    seen: set[str] = set()
    for item in experiments:
        if not isinstance(item, dict):
            raise ValueError("each experiment must be an object")
        experiment_id = item.get("id")
        if not isinstance(experiment_id, str) or not experiment_id:
            raise ValueError("each experiment requires id")
        if experiment_id in seen:
            raise ValueError(f"duplicate experiment id: {experiment_id}")
        seen.add(experiment_id)
        if item.get("kind") not in {"structured_demo_audit"}:
            raise ValueError(f"unsupported experiment kind: {item.get('kind')}")
        rows = item.get("rows", 200)
        if not isinstance(rows, int) or isinstance(rows, bool) or rows < 20:
            raise ValueError("structured_demo_audit rows must be an integer >= 20")


def _run_structured_demo(experiment: dict[str, Any], seed: int) -> dict[str, object]:
    rows = int(experiment.get("rows", 200))
    raw = build_dataset(n=rows, seed=seed)
    profiles = profile_dataframe(raw)
    backend = DemoBackend()
    synthetic = backend.generate(raw, profiles, seed=seed)
    audit = audit_dataset(raw, synthetic, profiles, backend.certified_for_egress)
    result = audit.to_dict()
    return {
        "rows": rows,
        "backend": backend.name,
        "metrics": {
            "audit_passed": int(bool(result["passed"])),
            "exact_row_overlap": int(result["exact_row_overlap"]),
            "identifier_overlap": int(result["identifier_overlap"]),
            "quasi_combo_overlap": int(result["quasi_combo_overlap"]),
            "rare_quasi_overlap": int(result["rare_quasi_overlap"]),
            "near_copy_rate": result["near_copy_rate"],
        },
        "reason_codes": list(result.get("reason_codes", [])),
    }


def run_suite(config_path: str | Path, out_dir: str | Path) -> dict[str, object]:
    config_file = Path(config_path).expanduser().resolve()
    out = Path(out_dir).expanduser().resolve()
    config = json.loads(config_file.read_text(encoding="utf-8"))
    validate_config(config)
    out.mkdir(parents=True, exist_ok=True)

    started_at = _utc_now()
    environment = environment_snapshot()
    runs_path = out / "runs.jsonl"
    records: list[dict[str, object]] = []

    for experiment in config["experiments"]:
        for seed in config["seeds"]:
            started = time.perf_counter()
            if experiment["kind"] == "structured_demo_audit":
                result = _run_structured_demo(experiment, seed)
            else:  # pragma: no cover - validate_config fails closed first
                raise ValueError(f"unsupported experiment kind: {experiment['kind']}")
            records.append(
                {
                    "schema_version": 1,
                    "suite": config["suite"],
                    "experiment_id": experiment["id"],
                    "kind": experiment["kind"],
                    "seed": seed,
                    "duration_seconds": round(time.perf_counter() - started, 6),
                    **result,
                }
            )

    with runs_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    manifest = {
        "schema_version": 1,
        "suite": config["suite"],
        "purpose": config.get("purpose"),
        "started_at": started_at,
        "finished_at": _utc_now(),
        "configuration": {
            "path": config_file.name,
            "sha256": _sha256(config_file),
        },
        "environment": environment,
        "experiment_ids": [item["id"] for item in config["experiments"]],
        "seeds": list(config["seeds"]),
        "run_count": len(records),
        "outputs": ["runs.jsonl"],
        "privacy_note": (
            "Manifest and normalized run records contain experiment metadata and aggregate "
            "metrics only; source rows and source narratives are not embedded."
        ),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a frozen Long Gate research suite.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    manifest = run_suite(args.config, args.out)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
