import json
from pathlib import Path

import pandas as pd

from longgate.audit import audit_dataset
from longgate.inspect import profile_dataframe
from longgate.profiles import get_profile
from longgate.release_ladder import resolve_release


def _frame(rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "participant_id": list(range(1000, 1000 + rows)),
            "age": [20 + (i % 3) for i in range(rows)],
            "score": [float(i) for i in range(rows)],
        }
    )


def test_reason_codes_distinguish_policy_from_technical_risk():
    raw = _frame()
    synthetic = raw.copy()
    profiles = profile_dataframe(raw)
    audit = audit_dataset(
        raw,
        synthetic,
        profiles,
        backend_certified=False,
        privacy_profile=get_profile("research"),
    )
    assert "backend_not_approved" in audit.reason_codes
    assert "profile_disallows_row_level" in audit.reason_codes
    assert "exact_row_overlap" in audit.reason_codes
    assert "identifier_overlap" in audit.reason_codes


def test_release_ladder_grants_aggregate_without_weakening_row_policy(tmp_path: Path):
    raw = _frame()
    synthetic = raw.copy()
    profiles = profile_dataframe(raw)
    profile = get_profile("research")
    audit = audit_dataset(
        raw,
        synthetic,
        profiles,
        backend_certified=False,
        privacy_profile=profile,
    )

    resolution, payload, scan = resolve_release(
        raw,
        profiles,
        profile,
        audit,
        tmp_path,
        row_level_payload=None,
    )

    assert resolution.workflow_status == "READY"
    assert resolution.row_level_release_allowed is False
    assert resolution.aggregate_fallback_used is True
    assert resolution.granted_release_class == "aggregate"
    assert payload is not None
    assert payload.name == "safe_aggregate.json"
    released = json.loads(payload.read_text(encoding="utf-8"))
    assert released["summary"]["n_rows_bucket"] == "10-19"
    assert "n_rows" not in released["summary"]
    for stats in released["summary"]["columns"].values():
        assert "n" not in stats
        assert "min" not in stats
        assert "max" not in stats
        assert set(stats) == {"n_bucket", "mean", "std"}
    assert released["summary"]["disclosure_controls"]["exact_counts_released"] is False
    assert released["summary"]["disclosure_controls"]["extrema_released"] is False
    assert scan["passed"] is True


def test_release_ladder_keeps_small_clinical_dataset_local(tmp_path: Path):
    raw = _frame(rows=10)
    synthetic = raw.copy()
    profiles = profile_dataframe(raw)
    profile = get_profile("clinical")
    audit = audit_dataset(
        raw,
        synthetic,
        profiles,
        backend_certified=False,
        privacy_profile=profile,
    )

    resolution, payload, _ = resolve_release(
        raw,
        profiles,
        profile,
        audit,
        tmp_path,
        row_level_payload=None,
    )

    assert resolution.workflow_status == "LOCAL_ONLY"
    assert resolution.granted_release_class is None
    assert payload is None
    assert resolution.aggregate_reason is not None
