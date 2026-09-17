from longgate.policy import PolicyEngine
from longgate.types import AuditResult, ReleaseClass


def _passing_audit() -> AuditResult:
    return AuditResult(
        passed=True,
        backend_certified=True,
        exact_row_overlap=0,
        identifier_overlap=0,
        quasi_combo_overlap=0,
        rare_quasi_overlap=0,
        near_copy_rate=0.0,
        free_text_columns=[],
        reasons=[],
        reason_codes=[],
    )


def test_raw_never_released():
    d = PolicyEngine().decide(ReleaseClass.RAW)
    assert d.allow is False


def test_pseudonymized_never_released():
    d = PolicyEngine().decide(ReleaseClass.PSEUDONYMIZED)
    assert d.allow is False


def test_passing_synthetic_audit_is_evidence_not_authorization():
    d = PolicyEngine().decide(ReleaseClass.SYNTHETIC, _passing_audit())
    assert d.allow is False
    assert "pre-1.0" in d.reason
    assert "evidence is not authorization" in d.reason


def test_aggregate_requires_explicit_guard_validation():
    unvalidated = PolicyEngine().decide(ReleaseClass.AGGREGATE)
    validated = PolicyEngine().decide(
        ReleaseClass.AGGREGATE,
        aggregate_validated=True,
    )
    assert unvalidated.allow is False
    assert validated.allow is True


def test_synthcity_is_not_egress_certified_in_v0_1():
    from longgate.backends.synthcity import SynthCityBackend

    assert SynthCityBackend.certified_for_egress is False
