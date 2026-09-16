from longgate.policy import PolicyEngine
from longgate.types import ReleaseClass


def test_raw_never_released():
    d = PolicyEngine().decide(ReleaseClass.RAW)
    assert d.allow is False


def test_pseudonymized_never_released():
    d = PolicyEngine().decide(ReleaseClass.PSEUDONYMIZED)
    assert d.allow is False


def test_synthcity_is_not_egress_certified_in_v0_1():
    from longgate.backends.synthcity import SynthCityBackend

    assert SynthCityBackend.certified_for_egress is False
