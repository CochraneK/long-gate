from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from longgate.semantic import audit_semantic_preview
from research.semantic_baselines import transform_baseline


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"red-team line {line_number} is not an object")
            for field in (
                "id",
                "attack_family",
                "source",
                "forbidden_literals",
                "utility_concepts",
            ):
                if field not in value:
                    raise ValueError(f"red-team line {line_number} missing {field}")
            case_id = value["id"]
            if not isinstance(case_id, str) or not case_id or case_id in seen:
                raise ValueError(f"invalid or duplicate red-team id at line {line_number}")
            seen.add(case_id)
            if not isinstance(value["source"], str) or not value["source"]:
                raise ValueError(f"red-team case {case_id} has empty source")
            if not isinstance(value["forbidden_literals"], list):
                raise ValueError(f"red-team case {case_id} forbidden_literals must be a list")
            utility = value["utility_concepts"]
            if not isinstance(utility, list) or not all(
                isinstance(group, list)
                and group
                and all(isinstance(term, str) and term for term in group)
                for group in utility
            ):
                raise ValueError(
                    f"red-team case {case_id} utility_concepts must be non-empty term groups"
                )
            cases.append(value)
    if not cases:
        raise ValueError("red-team corpus is empty")
    return cases


def _literal_reuse(candidate: str, literals: list[str]) -> int:
    normalized = candidate.casefold()
    return sum(1 for literal in literals if str(literal).casefold() in normalized)


def _utility_retention(candidate: str, concept_groups: list[list[str]]) -> float:
    normalized = candidate.casefold()
    retained = sum(
        1
        for alternatives in concept_groups
        if any(term.casefold() in normalized for term in alternatives)
    )
    return round(retained / len(concept_groups), 6) if concept_groups else 1.0


def evaluate_case(
    case: dict[str, Any],
    candidate: str,
    *,
    baseline: str,
) -> dict[str, object]:
    audit = audit_semantic_preview(str(case["source"]), candidate)
    forbidden_reuse = _literal_reuse(candidate, list(case["forbidden_literals"]))
    utility_retention = _utility_retention(candidate, list(case["utility_concepts"]))
    attack_success = int(
        audit.direct_pii_hits > 0
        or audit.reused_number_tokens > 0
        or forbidden_reuse > 0
    )
    return {
        "schema_version": 1,
        "experiment_id": f"semantic-redteam:{baseline}",
        "case_id": str(case["id"]),
        "attack_family": str(case["attack_family"]),
        "baseline": baseline,
        "metrics": {
            "attack_success": attack_success,
            "direct_pii_hits": audit.direct_pii_hits,
            "reused_number_tokens": audit.reused_number_tokens,
            "forbidden_literal_reuse": forbidden_reuse,
            "character_ngram_reuse_rate": audit.character_ngram_reuse_rate,
            "distinctive_token_reuse_rate": audit.distinctive_token_reuse_rate,
            "utility_retention_rate": utility_retention,
            "manual_review_eligible": int(
                audit.release_evidence.eligible_for_manual_review
            ),
        },
        "failed_conditions": list(audit.release_evidence.failed_conditions),
    }


def run_redteam(
    corpus_path: str | Path,
    baselines: list[str],
    *,
    model_path: str | Path | None = None,
) -> list[dict[str, object]]:
    cases = load_cases(corpus_path)
    records: list[dict[str, object]] = []
    for baseline in baselines:
        for case in cases:
            candidate = transform_baseline(
                baseline,
                str(case["source"]),
                model_path=model_path,
            )
            records.append(evaluate_case(case, candidate, baseline=baseline))
    return records


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_family: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        baseline = str(record["baseline"])
        family = str(record["attack_family"])
        grouped[baseline].append(record)
        by_family[(baseline, family)].append(record)

    def summarize_group(group: list[dict[str, object]]) -> dict[str, object]:
        metrics = [record["metrics"] for record in group]
        numeric = {
            key: _mean([float(item[key]) for item in metrics])
            for key in (
                "attack_success",
                "direct_pii_hits",
                "reused_number_tokens",
                "forbidden_literal_reuse",
                "character_ngram_reuse_rate",
                "distinctive_token_reuse_rate",
                "utility_retention_rate",
                "manual_review_eligible",
            )
        }
        return {"cases": len(group), "mean_metrics": numeric}

    baselines: dict[str, object] = {}
    for baseline, group in sorted(grouped.items()):
        families = {
            family: summarize_group(by_family[(baseline, family)])
            for family in sorted(
                {str(record["attack_family"]) for record in group}
            )
        }
        baselines[baseline] = {
            **summarize_group(group),
            "by_attack_family": families,
        }

    return {
        "schema_version": 1,
        "record_count": len(records),
        "baselines": baselines,
        "interpretation_note": (
            "This synthetic corpus is a controlled red-team/development instrument. "
            "Its rates are not population estimates and are not proof of anonymity."
        ),
    }


def write_outputs(records: list[dict[str, object]], out_dir: str | Path) -> dict[str, object]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    records_path = out / "semantic-redteam-runs.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary = summarize(records)
    (out / "semantic-redteam-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic semantic privacy red-team cases.")
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument(
        "--baseline",
        action="append",
        dest="baselines",
        required=True,
        help="Repeat for multiple baselines, e.g. identity and deterministic-regex.",
    )
    parser.add_argument("--model", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    records = run_redteam(args.corpus, args.baselines, model_path=args.model)
    summary = write_outputs(records, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
