from pathlib import Path

import pandas as pd

from longgate.egress import stage_egress, stage_json_egress
from longgate.policy import PolicyDecision
from longgate.types import ReleaseClass


def _allow() -> PolicyDecision:
    return PolicyDecision(True, ReleaseClass.SYNTHETIC, "test allow")


def test_final_scan_blocks_direct_pii(tmp_path: Path):
    df = pd.DataFrame({"note": ["email person@example.com"]})
    payload, scan = stage_egress(df, tmp_path, _allow())
    assert payload is None
    assert scan["passed"] is False
    assert scan["pii_hits"] >= 1


def test_final_scan_allows_clean_payload(tmp_path: Path):
    df = pd.DataFrame({"score": [1, 2, 3], "group": ["A", "B", "A"]})
    payload, scan = stage_egress(df, tmp_path, _allow())
    assert scan["passed"] is True
    assert payload is not None
    assert payload.exists()


def test_aggregate_json_egress(tmp_path: Path):
    decision = PolicyDecision(True, ReleaseClass.AGGREGATE, "aggregate allow")
    payload, scan = stage_json_egress(
        {"n_rows": 10, "mean": 2.5},
        tmp_path,
        decision,
    )
    assert scan["passed"] is True
    assert payload is not None
    assert payload.name == "safe_aggregate.json"


def test_aggregate_json_egress_blocks_pii_in_structured_key(tmp_path: Path):
    decision = PolicyDecision(True, ReleaseClass.AGGREGATE, "aggregate allow")
    payload, scan = stage_json_egress(
        {
            "summary": {
                "person@example.com": {
                    "n_bucket": "10-19",
                    "mean": 2.5,
                    "std": 0.4,
                }
            }
        },
        tmp_path,
        decision,
    )
    assert payload is None
    assert scan["passed"] is False
    assert scan["pii_hits"] >= 1
