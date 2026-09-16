import pytest

from longgate.profiles import (
    get_profile,
    list_profiles,
)


def test_all_builtin_profiles_keep_row_egress_closed():
    for profile in list_profiles():
        assert profile.row_level_synthetic_egress is False


def test_clinical_preset_is_more_conservative_than_research():
    research = get_profile("research")
    clinical = get_profile("clinical")
    assert clinical.min_dataset_size >= research.min_dataset_size
    assert clinical.min_group_size >= research.min_group_size
    assert clinical.rare_k >= research.rare_k
    assert (
        clinical.max_near_copy_rate
        <= research.max_near_copy_rate
    )


def test_unknown_profile_fails_closed():
    with pytest.raises(ValueError):
        get_profile("unknown")
