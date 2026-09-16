from longgate.purpose import DisclosureMode, route_purpose


def test_exact_statistics_stays_local():
    assert route_purpose("regression").mode == DisclosureMode.LOCAL_EXACT


def test_unknown_purpose_is_blocked():
    assert route_purpose("do whatever").mode == DisclosureMode.BLOCK
