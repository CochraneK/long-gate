from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import uuid

from . import __version__
from .audit import audit_dataset
from .backends import get_backend
from .egress import stage_egress
from .inspect import profile_dataframe
from .io import load_table, save_table
from .policy import PolicyEngine
from .report import build_report
from .types import ReleaseClass
from .utils import sha256_file, utc_now, write_json


@dataclass
class RunResult:
    run_id: str
    out_dir: Path
    report_path: Path
    synthetic_path: Path
    staged_payload: Path | None
    status: str


def run_pipeline(input_path: str | Path, out_root: str | Path = "./longgate-runs", backend_name: str = "demo", seed: int = 42) -> RunResult:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    run_id = f"LG-{uuid.uuid4().hex[:12]}"
    out_dir = Path(out_root).resolve() / run_id
    safe_dir = out_dir / "safe"
    report_dir = out_dir / "report"
    safe_dir.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, str]] = []
    def event(name: str, detail: str) -> None:
        events.append({"time": utc_now(), "name": name, "detail": detail})
    event("Run started", "Trusted local pipeline initialized; no cloud client is loaded by v0.1.")
    input_hash = sha256_file(input_path)
    event("Source registered", "Input hash recorded. Source rows are never written into the trust report.")
    df = load_table(input_path)
    event("Table loaded", f"Loaded {len(df)} rows and {len(df.columns)} columns in the local worker.")
    profiles = profile_dataframe(df)
    event("Schema classified", "Columns classified as identifier, quasi-identifier, sensitive, general, or free text.")
    backend = get_backend(backend_name)
    syn = backend.generate(df, profiles, seed=seed)
    event("Synthetic data generated", f"Backend={backend.name}; no deterministic real-to-fake identity mapping is retained.")
    synthetic_path = safe_dir / "synthetic.csv"
    save_table(syn, synthetic_path)
    event("Synthetic artifact staged locally", "Synthetic table written to the safe workspace.")
    audit = audit_dataset(df, syn, profiles, backend.certified_for_egress)
    event("Privacy audit completed", "PASS" if audit.passed else "BLOCKED: " + "; ".join(audit.reasons))
    decision = PolicyEngine().decide(ReleaseClass.SYNTHETIC, audit)
    event("Policy evaluated", f"allow={decision.allow}; {decision.reason}")
    staged_payload = stage_egress(syn, out_dir, decision)
    if staged_payload:
        event("Egress payload staged", "Safe payload created locally. v0.1 does not transmit it over the network.")
    else:
        event("Egress blocked", "No safe payload was created for network use.")
    manifest = {"run_id": run_id, "version": __version__, "input": {"filename": input_path.name, "sha256": input_hash, "rows": len(df), "columns": len(df.columns)}, "backend": backend.name, "backend_certified_for_egress": backend.certified_for_egress, "profiles": [p.to_dict() for p in profiles], "audit": audit.to_dict(), "decision": decision.to_dict(), "events": events, "network": {"cloud_client_loaded": False, "network_transmission_performed": False, "note": "v0.1 stages an eligible payload but never sends it."}}
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "audit.json", audit.to_dict())
    status = "PASS" if decision.allow else "BLOCKED"
    report_data = {"status": status, "rows": len(df), "columns": len(df.columns), "backend": backend.name, "profiles": [p.to_dict() for p in profiles], "audit": audit.to_dict(), "decision": decision.to_dict(), "events": events, "run_id": run_id, "input_sha256": input_hash, "version": __version__}
    report_path = report_dir / "trust-report.html"
    build_report(report_data, report_path)
    return RunResult(run_id=run_id, out_dir=out_dir, report_path=report_path, synthetic_path=synthetic_path, staged_payload=staged_payload, status=status)
