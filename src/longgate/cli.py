from __future__ import annotations

import argparse
import json
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="longgate", description="Long Gate — local-first privacy orchestration for safe AI data access.")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run the local inspect → synthesize → audit → gate → report pipeline.")
    run.add_argument("input", help="CSV, XLSX, JSON, or Parquet file")
    run.add_argument("--out", default="./longgate-runs", help="Output root directory")
    run.add_argument("--backend", default="demo", help="Synthetic backend: demo, synthcity, or synthcity:<plugin>. Demo can never pass egress.")
    run.add_argument("--seed", type=int, default=42)
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        result = run_pipeline(args.input, args.out, args.backend, args.seed)
        print(json.dumps({"run_id": result.run_id, "status": result.status, "output": str(result.out_dir), "report": str(result.report_path), "synthetic": str(result.synthetic_path), "safe_payload": str(result.staged_payload) if result.staged_payload else None}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
